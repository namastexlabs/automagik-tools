# JSON to Google Docs MCP Tool

Convert JSON data to DOCX files using Google Docs templates with placeholder substitution and markdown support.

## Features

- 📄 **JSON to DOCX Conversion**: Convert any JSON data to formatted Word documents
- 🔄 **Template Substitution**: Use `{{key}}` placeholders in Google Docs templates  
- 📝 **Markdown Support**: Convert markdown syntax to Word formatting
- ☁️ **Google Drive Integration**: Upload, share, and manage documents
- 📋 **Template Management**: Upload and manage DOCX templates
- ✅ **Data Validation**: Validate JSON data against template placeholders
- 🔐 **Service Account Auth**: Secure authentication using Google service accounts

## Setup

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API and Google Docs API
4. Create a service account:
   - Go to "Credentials" → "Create Credentials" → "Service Account"
   - Download the JSON key file
   - Share your Google Drive folders with the service account email

### 2. Configuration

Set up environment variables:

```bash
# Service account credentials (choose one method)
GOOGLE_DOCS_SERVICE_ACCOUNT_JSON="/path/to/service-account.json"
# OR
GOOGLE_DOCS_SERVICE_ACCOUNT_JSON_CONTENT='{"type": "service_account",...}'

# Optional settings
GOOGLE_DOCS_DEFAULT_FOLDER_ID="your-folder-id"
GOOGLE_DOCS_ENABLE_MARKDOWN_CONVERSION=true
GOOGLE_DOCS_DEFAULT_SHARE_TYPE=reader
GOOGLE_DOCS_TIMEOUT=300
```

### 3. Usage

#### Command Line
```bash
# Run with stdio transport
uvx automagik-tools tool json-to-google-docs --transport stdio

# Run with HTTP server
uvx automagik-tools tool json-to-google-docs --transport http --port 8000
```

#### MCP Configuration for Claude/Cursor
```json
{
  "mcpServers": {
    "json-to-google-docs": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "json-to-google-docs", "--transport", "stdio"],
      "env": {
        "GOOGLE_DOCS_SERVICE_ACCOUNT_JSON": "/path/to/service-account.json"
      }
    }
  }
}
```

## Available Functions

### 1. `convert_json_to_docs`
Convert JSON data to DOCX using a Google Docs template.

**Parameters:**
- `json_data`: JSON data as string or file path
- `template_id`: Google Docs template ID
- `output_filename`: Name for generated DOCX file
- `folder_id`: Google Drive folder ID (optional)
- `share_with_emails`: List of emails to share with (optional)
- `make_public`: Make document public (optional)

### 2. `upload_template`
Upload a DOCX file as a template to Google Drive.

**Parameters:**
- `file_path`: Path to DOCX file to upload
- `template_name`: Name for the template
- `folder_id`: Google Drive folder ID (optional)

### 3. `share_document`
Share a Google Docs document with users.

**Parameters:**
- `file_id`: Google Drive file ID
- `emails`: List of email addresses to share with
- `role`: Permission role (reader, commenter, writer)
- `make_public`: Make document public

### 4. `list_templates`
List available Google Docs templates.

**Parameters:**
- `folder_id`: Folder ID to search in (optional)
- `search_query`: Search query for templates (optional)

### 5. `download_document`
Download a Google Docs document in specified format.

**Parameters:**
- `file_id`: Google Drive file ID
- `output_path`: Local path to save file
- `format`: Export format (docx, pdf, txt)

### 6. `extract_placeholders`
Extract placeholder `{{keys}}` from a Google Docs template.

**Parameters:**
- `template_id`: Google Docs template ID

### 7. `validate_json_data`
Validate JSON data and optionally check against template placeholders.

**Parameters:**
- `json_data`: JSON data as string or file path
- `template_id`: Template ID to validate against (optional)

## Template Placeholders

Use `{{key}}` syntax in your Google Docs templates:

```
Hello {{user.name}},

Your order details:
- Order ID: {{order.id}}
- Total: ${{order.total}}
- Items: {{order.items}}

Thank you for your business!
```

## JSON Flattening

Nested JSON is automatically flattened using dot notation:

```json
{
  "user": {
    "name": "John Doe",
    "profile": {
      "email": "john@example.com"
    }
  },
  "order": {
    "id": "12345",
    "items": ["Item 1", "Item 2"]
  }
}
```

Becomes:
- `{{user.name}}` → "John Doe"
- `{{user.profile.email}}` → "john@example.com"  
- `{{order.id}}` → "12345"
- `{{order.items}}` → "Item 1, Item 2"

## Markdown Support

When enabled, markdown syntax is converted to Word formatting:

- `**bold**` → **bold text**
- `*italic*` → *italic text*
- `# Heading` → Heading 1
- `## Subheading` → Heading 2
- `` `code` `` → monospace text

## Error Handling

The tool provides comprehensive error handling:

- Invalid JSON data
- Missing service account credentials
- Google API errors
- Template not found
- Permission errors

## Security

- Uses Google service account authentication
- No API keys stored in code
- Secure credential management
- Optional fixed recipient mode

## Troubleshooting

### Common Issues

1. **"Service account credentials not found"**
   - Check environment variable is set correctly
   - Verify JSON file path exists
   - Ensure JSON content is valid

2. **"Permission denied"**
   - Share Google Drive folders with service account email
   - Check service account has necessary permissions

3. **"Template not found"**
   - Verify template ID is correct
   - Ensure service account has access to template

4. **"Invalid JSON data"**
   - Check JSON syntax is valid
   - Verify file path exists if using file input

### Getting Help

- Check Google Cloud Console for API quotas
- Verify service account permissions
- Review error messages for specific issues

## License

MIT License