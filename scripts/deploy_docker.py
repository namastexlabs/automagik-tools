#!/usr/bin/env python3
"""
Docker deployment automation for AutoMagik Tools MCP servers.
Supports deployment to Railway, Fly.io, and Render.
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint

console = Console()

SUPPORTED_PROVIDERS = ["railway", "aws", "gcloud", "render"]
TRANSPORT_TYPES = ["sse", "http", "stdio"]


class CloudDeployer:
    def __init__(self, provider: str, transport: str = "sse"):
        self.provider = provider.lower()
        self.transport = transport.lower()
        self.project_root = Path(__file__).parent.parent
        
        if self.provider not in SUPPORTED_PROVIDERS:
            console.print(f"[red]Error: Provider '{provider}' not supported[/red]")
            console.print(f"Supported providers: {', '.join(SUPPORTED_PROVIDERS)}")
            sys.exit(1)
            
        if self.transport not in TRANSPORT_TYPES:
            console.print(f"[red]Error: Transport '{transport}' not supported[/red]")
            console.print(f"Supported transports: {', '.join(TRANSPORT_TYPES)}")
            sys.exit(1)

    def check_prerequisites(self) -> bool:
        """Check if required tools are installed."""
        tools = {
            "railway": ["railway"],
            "aws": ["aws", "docker"],
            "gcloud": ["gcloud", "docker"],
            "render": ["render"]
        }
        
        required_tools = tools.get(self.provider, [])
        required_tools.append("docker")
        
        missing = []
        for tool in required_tools:
            if not shutil.which(tool):
                missing.append(tool)
        
        if missing:
            console.print(Panel(
                f"[red]Missing required tools: {', '.join(missing)}[/red]\n\n"
                f"Please install them before continuing.",
                title="Prerequisites Check Failed"
            ))
            
            # Provide installation instructions
            if "docker" in missing:
                console.print("\n[yellow]Docker:[/yellow] https://docs.docker.com/get-docker/")
            if "railway" in missing:
                console.print("\n[yellow]Railway CLI:[/yellow] npm install -g @railway/cli")
            if "aws" in missing:
                console.print("\n[yellow]AWS CLI:[/yellow] https://aws.amazon.com/cli/")
            if "gcloud" in missing:
                console.print("\n[yellow]Google Cloud SDK:[/yellow] https://cloud.google.com/sdk/docs/install")
            if "render" in missing:
                console.print("\n[yellow]Render CLI:[/yellow] https://render.com/docs/cli")
            
            return False
        
        return True

    def build_docker_image(self) -> bool:
        """Build the Docker image for deployment."""
        console.print(f"\n[cyan]Building Docker image for {self.transport} transport...[/cyan]")
        
        dockerfile = f"deploy/docker/Dockerfile.{self.transport}"
        image_tag = f"automagik-tools:{self.transport}"
        
        try:
            subprocess.run(
                ["docker", "build", "-f", dockerfile, "-t", image_tag, "."],
                cwd=self.project_root,
                check=True
            )
            console.print(f"[green]✓ Docker image built: {image_tag}[/green]")
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Failed to build Docker image: {e}[/red]")
            return False

    def deploy_to_railway(self):
        """Deploy to Railway."""
        console.print(Panel(
            "Railway deployment will:\n"
            "1. Create a new Railway project\n"
            "2. Deploy your Docker container\n"
            "3. Set up environment variables\n"
            "4. Provide you with a public URL",
            title="Railway Deployment"
        ))
        
        if not Confirm.ask("\nProceed with Railway deployment?"):
            return
        
        # Check if logged in
        try:
            subprocess.run(["railway", "whoami"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            console.print("[yellow]Please log in to Railway first[/yellow]")
            subprocess.run(["railway", "login"])
        
        # Create railway.toml
        railway_config = {
            "build": {
                "builder": "DOCKERFILE",
                "dockerfilePath": f"deploy/docker/Dockerfile.{self.transport}"
            },
            "deploy": {
                "startCommand": f"python -m automagik_tools serve-all --transport {self.transport} --host 0.0.0.0 --port ${{PORT}}",
                "restartPolicyType": "ON_FAILURE",
                "restartPolicyMaxRetries": 3
            }
        }
        
        railway_toml_path = self.project_root / "railway.toml"
        with open(railway_toml_path, "w") as f:
            import toml
            toml.dump(railway_config, f)
        
        console.print("[cyan]Initializing Railway project...[/cyan]")
        
        try:
            # Initialize project
            subprocess.run(["railway", "link"], cwd=self.project_root, check=True)
            
            # Deploy
            console.print("[cyan]Deploying to Railway...[/cyan]")
            subprocess.run(["railway", "up"], cwd=self.project_root, check=True)
            
            # Get URL
            result = subprocess.run(
                ["railway", "open"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            console.print(Panel(
                "[green]✓ Deployment successful![/green]\n\n"
                "Your MCP server is now live on Railway.\n"
                "Use 'railway logs' to view logs.\n"
                "Use 'railway open' to view in browser.",
                title="Success"
            ))
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Deployment failed: {e}[/red]")
        finally:
            # Clean up
            if railway_toml_path.exists():
                railway_toml_path.unlink()

    def deploy_to_aws(self):
        """Deploy to AWS (ECS with Fargate or App Runner)."""
        console.print(Panel(
            "AWS deployment options:\n"
            "1. AWS App Runner - Serverless, auto-scaling\n"
            "2. ECS with Fargate - More control, container orchestration\n"
            "3. Elastic Beanstalk - PaaS solution",
            title="AWS Deployment"
        ))
        
        deployment_type = Prompt.ask(
            "Choose deployment type",
            choices=["app-runner", "ecs-fargate", "elastic-beanstalk"],
            default="app-runner"
        )
        
        if deployment_type == "app-runner":
            self._deploy_to_app_runner()
        elif deployment_type == "ecs-fargate":
            self._deploy_to_ecs_fargate()
        else:
            self._deploy_to_elastic_beanstalk()

    def _deploy_to_app_runner(self):
        """Deploy to AWS App Runner."""
        console.print("[cyan]Deploying to AWS App Runner...[/cyan]")
        
        # Check AWS credentials
        try:
            subprocess.run(["aws", "sts", "get-caller-identity"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            console.print("[red]AWS credentials not configured. Run 'aws configure'[/red]")
            return
        
        region = Prompt.ask("AWS Region", default="us-east-1")
        service_name = Prompt.ask("Service name", default=f"automagik-{self.transport}")
        
        # Build and push to ECR
        console.print("[cyan]Building and pushing Docker image to ECR...[/cyan]")
        
        # Create ECR repository
        try:
            subprocess.run([
                "aws", "ecr", "create-repository",
                "--repository-name", service_name,
                "--region", region
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            console.print("[yellow]ECR repository may already exist[/yellow]")
        
        # Get ECR login token
        account_id = subprocess.check_output([
            "aws", "sts", "get-caller-identity",
            "--query", "Account",
            "--output", "text"
        ]).decode().strip()
        
        ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{service_name}"
        
        # Docker login to ECR
        subprocess.run([
            "aws", "ecr", "get-login-password",
            "--region", region
        ], capture_output=True).stdout.decode().strip()
        
        subprocess.run([
            "docker", "tag",
            f"automagik-tools:{self.transport}",
            f"{ecr_uri}:latest"
        ], check=True)
        
        subprocess.run([
            "docker", "push",
            f"{ecr_uri}:latest"
        ], check=True)
        
        # Create App Runner service
        console.print("[cyan]Creating App Runner service...[/cyan]")
        
        app_runner_config = {
            "ServiceName": service_name,
            "SourceConfiguration": {
                "ImageRepository": {
                    "ImageIdentifier": f"{ecr_uri}:latest",
                    "ImageConfiguration": {
                        "Port": str(8000 if self.transport == "sse" else 8080),
                        "RuntimeEnvironmentVariables": {
                            "TRANSPORT": self.transport,
                            "HOST": "0.0.0.0"
                        }
                    },
                    "ImageRepositoryType": "ECR"
                },
                "AutoDeploymentsEnabled": False
            }
        }
        
        import json
        config_file = self.project_root / "apprunner.json"
        with open(config_file, "w") as f:
            json.dump(app_runner_config, f, indent=2)
        
        try:
            result = subprocess.run([
                "aws", "apprunner", "create-service",
                "--cli-input-json", f"file://{config_file}",
                "--region", region
            ], capture_output=True, text=True)
            
            console.print(Panel(
                "[green]✓ Deployment successful![/green]\n\n"
                f"Service: {service_name}\n"
                f"Region: {region}\n\n"
                "View in AWS Console:\n"
                f"https://console.aws.amazon.com/apprunner/home?region={region}",
                title="Success"
            ))
        finally:
            if config_file.exists():
                config_file.unlink()

    def _deploy_to_ecs_fargate(self):
        """Deploy to ECS with Fargate."""
        console.print(Panel(
            "[yellow]ECS Fargate deployment requires more setup.[/yellow]\n\n"
            "Recommended steps:\n"
            "1. Use AWS Copilot CLI for easier deployment\n"
            "2. Or use the AWS Console ECS wizard\n"
            "3. Or use Terraform/CloudFormation\n\n"
            "Install Copilot: https://aws.github.io/copilot-cli/",
            title="ECS Fargate"
        ))

    def _deploy_to_elastic_beanstalk(self):
        """Deploy to Elastic Beanstalk."""
        console.print(Panel(
            "[yellow]Elastic Beanstalk deployment:[/yellow]\n\n"
            "1. Install EB CLI: pip install awsebcli\n"
            "2. Run: eb init -p docker\n"
            "3. Run: eb create automagik-env\n"
            "4. Run: eb deploy",
            title="Elastic Beanstalk"
        ))

    def deploy_to_gcloud(self):
        """Deploy to Google Cloud (Cloud Run or GKE)."""
        console.print(Panel(
            "Google Cloud deployment options:\n"
            "1. Cloud Run - Serverless, auto-scaling\n"
            "2. GKE (Kubernetes) - Full container orchestration",
            title="Google Cloud Deployment"
        ))
        
        deployment_type = Prompt.ask(
            "Choose deployment type",
            choices=["cloud-run", "gke"],
            default="cloud-run"
        )
        
        if deployment_type == "cloud-run":
            self._deploy_to_cloud_run()
        else:
            self._deploy_to_gke()

    def _deploy_to_cloud_run(self):
        """Deploy to Google Cloud Run."""
        console.print("[cyan]Deploying to Google Cloud Run...[/cyan]")
        
        # Check gcloud auth
        try:
            subprocess.run(["gcloud", "auth", "list"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            console.print("[yellow]Please authenticate with Google Cloud[/yellow]")
            subprocess.run(["gcloud", "auth", "login"])
        
        project_id = Prompt.ask("Google Cloud Project ID")
        region = Prompt.ask("Region", default="us-central1")
        service_name = Prompt.ask("Service name", default=f"automagik-{self.transport}")
        
        # Configure project
        subprocess.run(["gcloud", "config", "set", "project", project_id], check=True)
        
        # Enable required APIs
        console.print("[cyan]Enabling required APIs...[/cyan]")
        subprocess.run([
            "gcloud", "services", "enable",
            "run.googleapis.com",
            "containerregistry.googleapis.com"
        ], check=True)
        
        # Build and push to GCR
        gcr_image = f"gcr.io/{project_id}/{service_name}"
        
        console.print("[cyan]Building and pushing to Google Container Registry...[/cyan]")
        subprocess.run([
            "docker", "tag",
            f"automagik-tools:{self.transport}",
            gcr_image
        ], check=True)
        
        subprocess.run([
            "docker", "push",
            gcr_image
        ], check=True)
        
        # Deploy to Cloud Run
        console.print("[cyan]Deploying to Cloud Run...[/cyan]")
        
        port = "8000" if self.transport == "sse" else "8080"
        
        try:
            subprocess.run([
                "gcloud", "run", "deploy", service_name,
                "--image", gcr_image,
                "--platform", "managed",
                "--region", region,
                "--port", port,
                "--allow-unauthenticated",
                "--set-env-vars", f"TRANSPORT={self.transport},HOST=0.0.0.0"
            ], check=True)
            
            # Get service URL
            result = subprocess.run([
                "gcloud", "run", "services", "describe", service_name,
                "--platform", "managed",
                "--region", region,
                "--format", "value(status.url)"
            ], capture_output=True, text=True, check=True)
            
            service_url = result.stdout.strip()
            
            console.print(Panel(
                "[green]✓ Deployment successful![/green]\n\n"
                f"Service URL: {service_url}\n"
                f"Service: {service_name}\n"
                f"Region: {region}\n\n"
                "View logs: gcloud run logs read --service={service_name}",
                title="Success"
            ))
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Deployment failed: {e}[/red]")

    def _deploy_to_gke(self):
        """Deploy to Google Kubernetes Engine."""
        console.print(Panel(
            "[yellow]GKE deployment requires Kubernetes knowledge.[/yellow]\n\n"
            "Recommended steps:\n"
            "1. Create GKE cluster: gcloud container clusters create\n"
            "2. Use kubectl to deploy\n"
            "3. Or use Google Cloud Console\n\n"
            "Learn more: https://cloud.google.com/kubernetes-engine/docs",
            title="GKE Deployment"
        ))

    def deploy_to_render(self):
        """Deploy to Render."""
        console.print(Panel(
            "Render deployment will:\n"
            "1. Create a new Web Service\n"
            "2. Deploy your Docker container\n"
            "3. Set up automatic deploys from GitHub\n"
            "4. Provide free SSL certificates",
            title="Render Deployment"
        ))
        
        if not Confirm.ask("\nProceed with Render deployment?"):
            return
        
        # Create render.yaml
        render_config = {
            "services": [{
                "type": "web",
                "name": "automagik-mcp",
                "runtime": "docker",
                "dockerfilePath": f"./deploy/docker/Dockerfile.{self.transport}",
                "envVars": [
                    {"key": "TRANSPORT", "value": self.transport},
                    {"key": "HOST", "value": "0.0.0.0"},
                    {"key": "PORT", "value": "8000" if self.transport == "sse" else "8080"}
                ],
                "healthCheckPath": "/health",
                "plan": "free"
            }]
        }
        
        render_yaml_path = self.project_root / "render.yaml"
        with open(render_yaml_path, "w") as f:
            import yaml
            yaml.dump(render_config, f)
        
        console.print(Panel(
            "[yellow]Render deployment requires GitHub integration.[/yellow]\n\n"
            "1. Push your code to GitHub\n"
            "2. Go to https://dashboard.render.com/\n"
            "3. Click 'New' > 'Web Service'\n"
            "4. Connect your GitHub repository\n"
            "5. Render will auto-detect render.yaml\n\n"
            f"Your render.yaml has been created at:\n{render_yaml_path}",
            title="Manual Steps Required"
        ))

    def deploy(self):
        """Main deployment method."""
        if not self.check_prerequisites():
            return
        
        if not self.build_docker_image():
            return
        
        # Show deployment info
        table = Table(title="Deployment Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Provider", self.provider.title())
        table.add_row("Transport", self.transport.upper())
        table.add_row("Docker Image", f"automagik-tools:{self.transport}")
        table.add_row("Port", "8000" if self.transport == "sse" else "8080")
        
        console.print(table)
        
        # Deploy based on provider
        if self.provider == "railway":
            self.deploy_to_railway()
        elif self.provider == "aws":
            self.deploy_to_aws()
        elif self.provider == "gcloud":
            self.deploy_to_gcloud()
        elif self.provider == "render":
            self.deploy_to_render()


@click.command()
@click.option(
    "--provider",
    type=click.Choice(SUPPORTED_PROVIDERS),
    required=True,
    help="Cloud provider to deploy to"
)
@click.option(
    "--transport",
    type=click.Choice(TRANSPORT_TYPES),
    default="sse",
    help="Transport type for the MCP server"
)
def main(provider: str, transport: str):
    """Deploy AutoMagik Tools MCP server to cloud providers."""
    console.print(Panel(
        f"[bold cyan]AutoMagik Tools Cloud Deployment[/bold cyan]\n"
        f"Provider: {provider.title()}\n"
        f"Transport: {transport.upper()}",
        title="🚀 Deployment Tool"
    ))
    
    deployer = CloudDeployer(provider, transport)
    deployer.deploy()


if __name__ == "__main__":
    main()