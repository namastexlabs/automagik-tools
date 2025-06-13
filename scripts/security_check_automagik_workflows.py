"""Security validation for automagik_workflows tool"""
import os
import re
from pathlib import Path

def check_security_patterns():
    """Check for security best practices"""
    results = {}
    
    # Define the tool directory
    tool_dir = Path("automagik_tools/tools/automagik_workflows")
    
    # Check all Python files in the tool
    python_files = list(tool_dir.glob("*.py"))
    
    for file_path in python_files:
        content = file_path.read_text()
        
        # Security checks
        security_issues = []
        
        # 1. Check for hardcoded secrets
        if re.search(r'Bearer\s+[a-zA-Z0-9]+', content):
            security_issues.append("Hardcoded Bearer token found")
        
        if re.search(r'sk-[a-zA-Z0-9]{48,}', content):
            security_issues.append("Hardcoded OpenAI API key found")
            
        if re.search(r'["\'][a-zA-Z0-9]{32,}["\']', content) and "test-" not in content:
            # Allow test keys but flag potential real keys
            if not any(test_word in content.lower() for test_word in ['test', 'mock', 'example', 'dummy']):
                security_issues.append("Potential hardcoded secret found")
        
        # 2. Check for unsafe code patterns
        if re.search(r'\beval\s*\(', content):
            security_issues.append("Use of eval() function found")
            
        if re.search(r'\bexec\s*\(', content):
            security_issues.append("Use of exec() function found")
            
        # 3. Check for proper auth handling
        has_auth_config = "api_key" in content and ("config" in content or "getattr" in content)
        has_auth_header = "Authorization" in content or "X-API-Key" in content
        
        # 4. Check for proper error handling (don't leak sensitive info)
        if re.search(r'print\s*\([^)]*api_key', content, re.IGNORECASE):
            security_issues.append("API key potentially logged in print statement")
            
        if re.search(r'logger?\.[^(]*\([^)]*api_key', content, re.IGNORECASE):
            security_issues.append("API key potentially logged in log statement")
        
        # 5. Check for SQL injection patterns (if any SQL)
        if re.search(r'f".*SELECT.*{', content) or re.search(r'".*SELECT.*"\s*%', content):
            security_issues.append("Potential SQL injection vulnerability")
        
        results[str(file_path)] = {
            "security_issues": security_issues,
            "has_auth_config": has_auth_config,
            "has_auth_header": has_auth_header,
            "file_size": len(content),
        }
    
    return results

def check_dependency_security():
    """Check dependencies for known security issues"""
    # Read requirements from config.py
    config_file = Path("automagik_tools/tools/automagik_workflows/config.py")
    content = config_file.read_text()
    
    # Basic dependency checks
    dependencies = []
    if "httpx" in content:
        dependencies.append("httpx")
    if "asyncio" in content:
        dependencies.append("asyncio")
    if "pydantic" in content:
        dependencies.append("pydantic")
    
    # Check for vulnerable patterns
    vulnerable_patterns = []
    
    # Check for unsafe HTTP configurations
    if "verify=False" in content:
        vulnerable_patterns.append("SSL verification disabled")
    
    if "trust_env=False" in content:
        vulnerable_patterns.append("Environment trust disabled (could be security issue)")
    
    return {
        "dependencies": dependencies,
        "vulnerable_patterns": vulnerable_patterns
    }

def main():
    """Run security validation"""
    print("🔒 Security Validation for AutoMagik Workflows")
    print("=" * 50)
    
    # Check security patterns
    security_results = check_security_patterns()
    
    total_issues = 0
    for file_path, result in security_results.items():
        if result["security_issues"]:
            print(f"\n❌ {file_path}:")
            for issue in result["security_issues"]:
                print(f"  - {issue}")
                total_issues += 1
        else:
            print(f"✅ {os.path.basename(file_path)}: No security issues found")
        
        # Check auth implementation
        if result["has_auth_config"] and result["has_auth_header"]:
            print(f"  ✅ Authentication properly implemented")
        elif not result["has_auth_config"] and not result["has_auth_header"]:
            print(f"  ℹ️  No authentication found (may be intentional)")
        else:
            print(f"  ⚠️  Partial authentication implementation")
    
    # Check dependencies
    print(f"\n📦 Dependency Security Check:")
    dep_results = check_dependency_security()
    
    print(f"Dependencies found: {', '.join(dep_results['dependencies'])}")
    
    if dep_results["vulnerable_patterns"]:
        print("❌ Security concerns:")
        for pattern in dep_results["vulnerable_patterns"]:
            print(f"  - {pattern}")
            total_issues += 1
    else:
        print("✅ No dependency security issues found")
    
    # Summary
    print(f"\n📊 Security Summary:")
    print(f"Total security issues: {total_issues}")
    
    if total_issues == 0:
        print("🎉 Security validation PASSED")
        return True
    elif total_issues <= 2:
        print("⚠️  Security validation PASSED with warnings")
        return True
    else:
        print("❌ Security validation FAILED")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)