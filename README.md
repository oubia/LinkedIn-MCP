# LinkedIn MCP Server

A Model Context Protocol (MCP) server implementation that integrates LinkedIn APIs with Claude Desktop, enabling automated job application workflows and LinkedIn profile management through conversational AI.

## Overview

This MCP server provides Claude Desktop with the ability to interact with LinkedIn's APIs, allowing you to:

- Search for job opportunities
- Apply to jobs automatically
- Manage your LinkedIn profile
- Network with connections
- Track application status
- Analyze job market trends

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [LinkedIn API Setup](#linkedin-api-setup)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Authentication](#authentication)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Prerequisites

Before setting up the LinkedIn MCP server, ensure you have:

- Python 3.8 or higher
- Claude Desktop application installed
- LinkedIn Developer Account
- Valid LinkedIn API credentials

## Installation

1. Clone this repository:
```bash
git clone https://github.com/oubia/LinkedIn-MCP.git
cd LinkedIn-MCP
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## LinkedIn API Setup

### 1. Create a LinkedIn Developer Application

1. Visit the [LinkedIn Developer Portal](https://developer.linkedin.com/)
2. Sign in with your LinkedIn account
3. Click "Create App" and fill in the required information:
   - App name: "LinkedIn MCP Server"
   - LinkedIn Page: Your personal or company page
   - Privacy policy URL: Required
   - App logo: Optional but recommended

### 2. Configure API Permissions

Request the following LinkedIn API products:
- **Sign In with LinkedIn using OpenID Connect**: For basic authentication
- **Marketing Developer Platform**: For job posting and company data access
- **Talent Solutions**: For job application and candidate management

### 3. Set Redirect URLs

Add the following redirect URL in your app settings:
```
http://localhost:8080/auth/linkedin/callback
```

### 4. Get Your API Credentials

After approval, note down:
- Client ID
- Client Secret
- These will be used in the configuration step

## Claude Desktop Configuration

### 1. Locate Claude Desktop Config

Find your Claude Desktop configuration file:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### 2. Add MCP Server Configuration

Add the LinkedIn MCP server to your Claude Desktop config:

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": [
        "/path/to/LinkedIn-MCP/src/linkedin_mcp_server.py"
      ],
      "env": {
        "LINKEDIN_CLIENT_ID": "your_client_id_here",
        "LINKEDIN_CLIENT_SECRET": "your_client_secret_here",
        "LINKEDIN_REDIRECT_URI": "http://localhost:8080/auth/linkedin/callback"
      }
    }
  }
}
```

### 3. Environment Variables

Create a `.env` file in the project root:

```env
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8080/auth/linkedin/callback
LINKEDIN_SCOPE=r_liteprofile,r_emailaddress,w_member_social
```

## Available Tools

The LinkedIn MCP server provides the following tools for Claude Desktop:

### Job Search and Applications

- `search_jobs`: Search for job opportunities based on criteria
- `get_job_details`: Retrieve detailed information about a specific job
- `apply_to_job`: Submit job applications automatically
- `get_application_status`: Check the status of submitted applications

### Profile Management

- `get_profile`: Retrieve your LinkedIn profile information
- `update_profile`: Update profile sections
- `get_profile_views`: Check who viewed your profile

### Networking

- `search_people`: Find LinkedIn users based on criteria
- `send_connection_request`: Send connection requests
- `get_connections`: Retrieve your network connections
- `send_message`: Send messages to connections

### Company Research

- `search_companies`: Find companies based on criteria
- `get_company_details`: Get detailed company information
- `follow_company`: Follow companies for updates

## Usage Examples

### Example 1: Job Search and Application

```
You: "Help me find software engineering jobs in San Francisco and apply to the most suitable ones"

Claude will:
1. Use search_jobs to find relevant positions
2. Analyze job requirements against your profile
3. Use apply_to_job for suitable positions
4. Provide a summary of applications submitted
```

### Example 2: Profile Optimization

```
You: "Analyze my LinkedIn profile and suggest improvements for software engineering roles"

Claude will:
1. Use get_profile to retrieve your current profile
2. Analyze skills, experience, and keywords
3. Suggest improvements based on job market trends
4. Help update your profile using update_profile
```

### Example 3: Network Expansion

```
You: "Find and connect with software engineers at Google"

Claude will:
1. Use search_people to find relevant professionals
2. Analyze profiles for connection worthiness
3. Send personalized connection requests
4. Track connection acceptance rates
```

## Authentication

The MCP server uses OAuth 2.0 for LinkedIn API authentication:

### Initial Setup

1. Start the MCP server
2. Claude Desktop will prompt for LinkedIn authentication
3. Complete the OAuth flow in your browser
4. Access token will be stored securely for future use

### Token Refresh

- Access tokens are automatically refreshed when needed
- Refresh tokens are securely stored
- Re-authentication is required if refresh tokens expire

## Configuration Options

### Job Search Preferences

Configure default job search parameters in `config.yaml`:

```yaml
job_search:
  default_location: "San Francisco, CA"
  default_keywords: ["software engineer", "full stack", "python"]
  experience_level: ["mid-level", "senior"]
  company_size: ["startup", "medium", "large"]
  remote_preference: "hybrid"

application:
  auto_apply: false
  cover_letter_template: "templates/cover_letter.txt"
  resume_path: "documents/resume.pdf"
```

### Rate Limiting

LinkedIn APIs have rate limits. Configure respectful usage:

```yaml
rate_limiting:
  requests_per_hour: 100
  requests_per_day: 500
  delay_between_requests: 1  # seconds
```

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: "Invalid client credentials"
```
- Verify your Client ID and Client Secret
- Ensure your LinkedIn app is approved for required permissions

**2. Rate Limiting**
```
Error: "API rate limit exceeded"
```
- Wait for the rate limit window to reset
- Adjust rate limiting configuration
- Consider upgrading your LinkedIn API plan

**3. Claude Desktop Connection Issues**
```
Error: "MCP server not responding"
```
- Check that Python and dependencies are properly installed
- Verify the path to the MCP server script in Claude config
- Check server logs for detailed error messages

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
LOG_LEVEL=debug
```

### Logs Location

Server logs are stored in:
- `logs/linkedin_mcp.log`
- `logs/api_requests.log`

## Security Considerations

- Never commit API credentials to version control
- Use environment variables for sensitive data
- Regularly rotate access tokens
- Monitor API usage for suspicious activity
- Follow LinkedIn's Terms of Service and API Usage Policy

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 src/
black src/

# Type checking
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and legitimate job search purposes only. Users must comply with LinkedIn's Terms of Service and API Usage Policy. Automated actions should be used responsibly and ethically.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review LinkedIn's API documentation

---

**Note**: This MCP server requires active LinkedIn API credentials and proper authentication setup. Ensure you have the necessary permissions and follow LinkedIn's guidelines for automated interactions.
