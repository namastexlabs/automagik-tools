# JSON to Google Docs Example

This example demonstrates how to use automagik-tools to convert JSON data into formatted Word documents using Google Docs templates with automatic placeholder substitution and markdown support.

## Use Case Description

Transform JSON data into professional documents for:
- Automated report generation from API data
- Invoice and receipt creation from order data
- Contract generation with customer information
- Certificate and diploma creation from student records
- Personalized letters and emails from CRM data
- Data export to shareable document formats

Perfect for automating document generation workflows, creating data-driven reports, and eliminating manual copy-paste work.

## Setup

### Prerequisites

1. **Google Cloud Project**: With Drive API and Docs API enabled
2. **Service Account**: JSON credentials file
3. **Google Drive Access**: Service account email added to shared folders
4. **Template Documents**: DOCX files with `{{placeholder}}` syntax

### Google Cloud Setup

#### Step 1: Create Project and Enable APIs

```bash
# Go to Google Cloud Console
https://console.cloud.google.com/

# Create new project or select existing
# Enable APIs:
# - Google Drive API
# - Google Docs API
```

#### Step 2: Create Service Account

```bash
# In Google Cloud Console:
# 1. Go to "IAM & Admin" → "Service Accounts"
# 2. Click "Create Service Account"
# 3. Name: "json-to-docs-service"
# 4. Grant role: "Editor" (or custom role with Drive/Docs access)
# 5. Click "Create Key" → "JSON"
# 6. Download the JSON key file
```

#### Step 3: Share Drive Folders

```bash
# Copy service account email from JSON file:
# "client_email": "json-to-docs-service@project-id.iam.gserviceaccount.com"

# In Google Drive:
# 1. Right-click folder → "Share"
# 2. Paste service account email
# 3. Grant "Editor" permission
```

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required - Service account credentials (choose one method)
GOOGLE_DOCS_SERVICE_ACCOUNT_JSON="/path/to/service-account.json"
# OR
GOOGLE_DOCS_SERVICE_ACCOUNT_JSON_CONTENT='{"type":"service_account","project_id":"..."}'

# Optional Configuration
GOOGLE_DOCS_DEFAULT_FOLDER_ID="1a2b3c4d5e6f7g8h9i0j"  # Default upload folder
GOOGLE_DOCS_ENABLE_MARKDOWN_CONVERSION=true           # Convert markdown syntax
GOOGLE_DOCS_DEFAULT_SHARE_TYPE=reader                 # Default sharing permission
GOOGLE_DOCS_TIMEOUT=300                               # Request timeout in seconds
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool json-to-google-docs --transport stdio

# Run with SSE transport
uvx automagik-tools tool json-to-google-docs --transport sse --port 8000

# Run with HTTP transport
uvx automagik-tools tool json-to-google-docs --transport http --port 8001
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "json-to-google-docs": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "json-to-google-docs",
        "--transport",
        "stdio"
      ],
      "env": {
        "GOOGLE_DOCS_SERVICE_ACCOUNT_JSON": "/path/to/service-account.json",
        "GOOGLE_DOCS_DEFAULT_FOLDER_ID": "your-folder-id",
        "GOOGLE_DOCS_ENABLE_MARKDOWN_CONVERSION": "true"
      }
    }
  }
}
```

### For Cursor

Add this to your Cursor MCP configuration (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "json-to-google-docs": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "json-to-google-docs",
        "--transport",
        "stdio"
      ],
      "env": {
        "GOOGLE_DOCS_SERVICE_ACCOUNT_JSON": "C:\\path\\to\\service-account.json",
        "GOOGLE_DOCS_DEFAULT_FOLDER_ID": "your-folder-id"
      }
    }
  }
}
```

## Expected Output

### 1. Creating Invoice from JSON

**Template (invoice-template.docx):**
```
INVOICE #{{invoice.number}}

Bill To:
{{customer.name}}
{{customer.address}}
{{customer.city}}, {{customer.state}} {{customer.zip}}

Date: {{invoice.date}}
Due Date: {{invoice.due_date}}

Items:
{{items}}

Subtotal: ${{invoice.subtotal}}
Tax ({{invoice.tax_rate}}%): ${{invoice.tax}}
Total: ${{invoice.total}}

Thank you for your business!
```

**JSON Data:**
```json
{
  "invoice": {
    "number": "INV-2024-001",
    "date": "2024-01-15",
    "due_date": "2024-02-15",
    "subtotal": "1000.00",
    "tax_rate": "8.5",
    "tax": "85.00",
    "total": "1085.00"
  },
  "customer": {
    "name": "Acme Corporation",
    "address": "123 Business St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102"
  },
  "items": "1. Web Development Services - $800.00\n2. Hosting (Annual) - $200.00"
}
```

**In Claude Desktop, say:**
```
Create a Google Doc from this JSON data using template ID 1a2b3c4d5e6f7g8h9i0j, save it as Invoice_INV-2024-001.docx in folder your-folder-id, and share it with client@example.com
```

**Claude responds:**
```json
{
  "status": "success",
  "file_id": "9z8y7x6w5v4u3t2s1r0q",
  "file_name": "Invoice_INV-2024-001.docx",
  "web_view_link": "https://docs.google.com/document/d/9z8y7x6w5v4u3t2s1r0q/edit",
  "download_link": "https://docs.google.com/document/d/9z8y7x6w5v4u3t2s1r0q/export?format=docx",
  "shared_with": ["client@example.com"],
  "placeholders_replaced": 15,
  "message": "Document created and shared successfully"
}
```

### 2. Upload Template

**In Claude Desktop, say:**
```
Upload the template file at /path/to/invoice-template.docx with the name "Invoice Template 2024" to folder your-templates-folder-id
```

**Claude responds:**
```json
{
  "status": "success",
  "template_id": "1a2b3c4d5e6f7g8h9i0j",
  "template_name": "Invoice Template 2024",
  "web_view_link": "https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/edit",
  "message": "Template uploaded successfully"
}
```

### 3. List Available Templates

**In Claude Desktop, say:**
```
List all templates in folder your-templates-folder-id that contain "invoice" in their name
```

**Claude responds:**
```json
{
  "status": "success",
  "templates": [
    {
      "id": "1a2b3c4d5e6f7g8h9i0j",
      "name": "Invoice Template 2024",
      "created_time": "2024-01-10T10:30:00Z",
      "modified_time": "2024-01-12T14:20:00Z",
      "web_view_link": "https://docs.google.com/document/d/1a2b3c4d5e6f7g8h9i0j/edit"
    },
    {
      "id": "2b3c4d5e6f7g8h9i0j1k",
      "name": "Invoice Template - Simple",
      "created_time": "2024-01-05T09:15:00Z",
      "modified_time": "2024-01-05T09:15:00Z",
      "web_view_link": "https://docs.google.com/document/d/2b3c4d5e6f7g8h9i0j1k/edit"
    }
  ],
  "total_count": 2
}
```

### 4. Extract Placeholders from Template

**In Claude Desktop, say:**
```
Extract all placeholders from template with ID 1a2b3c4d5e6f7g8h9i0j
```

**Claude responds:**
```json
{
  "status": "success",
  "template_id": "1a2b3c4d5e6f7g8h9i0j",
  "placeholders": [
    "invoice.number",
    "invoice.date",
    "invoice.due_date",
    "invoice.subtotal",
    "invoice.tax_rate",
    "invoice.tax",
    "invoice.total",
    "customer.name",
    "customer.address",
    "customer.city",
    "customer.state",
    "customer.zip",
    "items"
  ],
  "total_count": 13,
  "nested_structure": {
    "invoice": ["number", "date", "due_date", "subtotal", "tax_rate", "tax", "total"],
    "customer": ["name", "address", "city", "state", "zip"],
    "root": ["items"]
  }
}
```

### 5. Validate JSON Data

**In Claude Desktop, say:**
```
Validate this JSON data against template ID 1a2b3c4d5e6f7g8h9i0j: {"invoice":{"number":"INV-001"},"customer":{"name":"Acme"}}
```

**Claude responds:**
```json
{
  "status": "success",
  "is_valid": false,
  "missing_placeholders": [
    "invoice.date",
    "invoice.due_date",
    "invoice.subtotal",
    "invoice.tax_rate",
    "invoice.tax",
    "invoice.total",
    "customer.address",
    "customer.city",
    "customer.state",
    "customer.zip",
    "items"
  ],
  "extra_keys": [],
  "warnings": [
    "Missing required placeholder: invoice.date",
    "Missing required placeholder: invoice.total",
    "Missing required placeholder: items"
  ],
  "message": "JSON data is missing some required placeholders"
}
```

## Real-World Usage Scenarios

### Scenario 1: Automated Monthly Reports

**In Claude Desktop, say:**
```
First, fetch data from the API at https://api.example.com/reports/monthly-sales

Then, create a document from the sales data using template ID monthly-report-template-id, save it as Sales_Report_{month}_{year}.docx in folder reports-folder-id, and share it with manager@example.com and ceo@example.com
```

**Claude does:**
- Fetches data from the API
- Creates a document from the sales data
- Shares it with the specified recipients

**Claude responds:**
```json
{
  "status": "success",
  "file_id": "9z8y7x6w5v4u3t2s1r0q",
  "file_name": "Sales_Report_January_2024.docx",
  "web_view_link": "https://docs.google.com/document/d/9z8y7x6w5v4u3t2s1r0q/edit",
  "shared_with": ["manager@example.com", "ceo@example.com"],
  "message": "Monthly sales report generated and shared successfully"
}
```

### Scenario 2: Bulk Certificate Generation

**In Claude Desktop, say:**
```
Generate certificates for these course completions:
- John Doe, Python 101, 2024-01-15, grade A
- Jane Smith, Python 101, 2024-01-15, grade A+

Use template ID certificate-template-id, save each as Certificate_{name}.docx in folder certificates-folder-id, and share with each student's email if provided
```

**Claude does:**
- Generates certificates for each student
- Saves them with appropriate filenames
- Shares them with the students

**Claude responds:**
```json
{
  "status": "success",
  "message": "Generated 2 certificates successfully",
  "certificates": [
    {
      "student": "John Doe",
      "file_name": "Certificate_John_Doe.docx",
      "web_view_link": "https://docs.google.com/document/d/9z8y7x6w5v4u3t2s1r0q/edit"
    },
    {
      "student": "Jane Smith",
      "file_name": "Certificate_Jane_Smith.docx",
      "web_view_link": "https://docs.google.com/document/d/8y7x6w5v4u3t2s1r0q9z/edit"
    }
  ]
}
```

### Scenario 3: Contract Generation with Markdown

**In Claude Desktop, say:**
```
Generate a contract with markdown formatting using this data:

Contract details:
- Number: CTR-2024-001
- Date: 2024-01-15
- Effective date: 2024-02-01

Client details:
- Name: **Acme Corporation**
- Representative: *John Doe, CEO*
- Address: 123 Business St, San Francisco, CA 94102

Terms:
## Payment Terms
- **Initial Payment**: 50% upfront
- **Final Payment**: 50% upon completion
- **Late Fee**: 5% per month

## Deliverables
1. Website design mockups
2. Responsive HTML/CSS implementation
3. Backend API development
4. Deployment and training

Total amount: $50,000

Use template ID contract-template-id, save as Contract_CTR-2024-001.docx in folder contracts-folder-id, and share with legal@example.com and client@acme.com
```

**Claude does:**
- Generates a contract with markdown formatting
- Saves it with the specified filename
- Shares it with the legal team and client

**Claude responds:**
```json
{
  "status": "success",
  "file_id": "7x6w5v4u3t2s1r0q9z8y",
  "file_name": "Contract_CTR-2024-001.docx",
  "web_view_link": "https://docs.google.com/document/d/7x6w5v4u3t2s1r0q9z8y/edit",
  "shared_with": ["legal@example.com", "client@acme.com"],
  "message": "Contract generated with markdown formatting and shared successfully"
}
```

### Scenario 4: Data Export Pipeline

**In Claude Desktop, say:**
```
Export database records to documents. First, query the customers.db database for all completed orders. Then, for each order, generate an order confirmation document using template ID order-confirmation-template-id, save as Order_{order_id}.docx in folder order-confirmations-folder-id, and share with the customer's email address.
```

**Claude does:**
- Queries the database for completed orders
- Generates order confirmation documents for each record
- Shares them with the respective customers

**Claude responds:**
```json
{
  "status": "success",
  "message": "Exported 15 order confirmations successfully",
  "orders_processed": 15,
  "folder_link": "https://drive.google.com/drive/folders/order-confirmations-folder-id"
}
```

## Features Demonstrated

1. **Placeholder Substitution**: Automatic `{{key}}` replacement with JSON values
2. **Nested JSON Support**: Dot notation for nested objects (`{{user.profile.email}}`)
3. **Markdown Conversion**: Convert markdown syntax to Word formatting
4. **Template Management**: Upload, list, and organize templates
5. **Sharing Controls**: Share documents with specific users or make public
6. **Validation**: Check JSON data against template requirements
7. **Batch Processing**: Generate multiple documents from arrays

## Template Placeholder Syntax

### Basic Placeholders
```
{{key}}                    → Simple value
{{nested.key}}             → Nested object
{{array.0}}                → Array index
{{user.profile.email}}     → Deep nesting
```

### Markdown Support (when enabled)
```
**{{bold_text}}**          → Bold formatting
*{{italic_text}}*          → Italic formatting
# {{heading}}              → Heading 1
## {{subheading}}          → Heading 2
`{{code}}`                 → Monospace/code
```

### Array Handling
```json
{
  "items": ["Item 1", "Item 2", "Item 3"]
}
```
Becomes: `{{items}}` → "Item 1, Item 2, Item 3"

Or with custom formatting:
```json
{
  "items": "1. Item 1\n2. Item 2\n3. Item 3"
}
```

## Best Practices

1. **Template Design**: Create clear, well-formatted templates in Word first
2. **Placeholder Naming**: Use descriptive, hierarchical names (e.g., `customer.billing.address`)
3. **Validation First**: Always validate JSON before generating documents
4. **Folder Organization**: Use separate folders for templates, outputs, and archives
5. **Error Handling**: Check response status before proceeding
6. **Batch Operations**: Process multiple documents with delays to avoid rate limits
7. **Security**: Never expose service account credentials in code

## Troubleshooting

### Common Issues

1. **"Service account credentials not found"**
   - Check `GOOGLE_DOCS_SERVICE_ACCOUNT_JSON` path is correct
   - Verify JSON file exists and is readable
   - Ensure JSON content is valid

2. **"Permission denied"**
   - Share Google Drive folders with service account email
   - Grant "Editor" permission to service account
   - Check folder ID is correct

3. **"Template not found"**
   - Verify template ID is correct
   - Ensure service account has access to template
   - Check template is in shared folder

4. **"Invalid JSON data"**
   - Validate JSON syntax by asking Claude to validate your JSON data against the template
   - Check for missing required fields
   - Verify nested structure matches template

5. **"Placeholders not replaced"**
   - Check placeholder syntax: `{{key}}` not `{key}` or `[[key]]`
   - Verify JSON keys match placeholder names exactly
   - Ask Claude to show the expected placeholders from your template

6. **"Markdown not converting"**
   - Enable markdown conversion: `GOOGLE_DOCS_ENABLE_MARKDOWN_CONVERSION=true`
   - Check markdown syntax is correct
   - Some complex markdown may not be supported

## Performance Tips

1. **Reuse Templates**: Upload templates once, reuse template IDs
2. **Batch Processing**: Add delays between bulk operations
3. **Folder Structure**: Organize by date/category for faster access
4. **Validation**: Validate data before conversion to avoid failed operations
5. **Caching**: Cache template IDs and folder IDs in your application

## Security Considerations

- **Service Account**: Use least-privilege permissions
- **Credentials**: Store JSON credentials securely, never in code
- **Sharing**: Only share with necessary recipients
- **Public Access**: Avoid making documents public unless required
- **Data Privacy**: Remove sensitive data before generating documents
- **Audit Logs**: Monitor service account activity in Google Cloud Console

## Next Steps

1. **Automate Workflows**: Integrate with CI/CD pipelines
2. **Create Template Library**: Build reusable template collection
3. **Add Webhooks**: Trigger document generation from events
4. **Implement Queue**: Handle high-volume generation with job queues
5. **Build UI**: Create web interface for non-technical users

## Additional Resources

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [Google Docs API Documentation](https://developers.google.com/docs/api)
- [Service Account Setup Guide](https://cloud.google.com/iam/docs/service-accounts)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
