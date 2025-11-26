# RCRA Dashboard

## Overview
Beautiful web-based dashboard for monitoring and analyzing RCRA (Root Cause & Remediation Assistant) incidents.

## Features
- 📊 **Real-time Statistics** - Total incidents, 24-hour activity, severity breakdown
- 📋 **Incident Management** - View, filter, and search all incidents
- 🔍 **Detailed Analysis** - Click any incident for full root cause analysis
- 🏷️ **Tag Cloud** - Most common error patterns and keywords
- 🔄 **Auto-refresh** - Data updates automatically every minute
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Quick Start

### 1. Get Your API Endpoint

After deploying the RCRA stack, get your API endpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name rcra-stack \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='DashboardAPIEndpoint'].OutputValue" \
  --output text
```

**Your API Endpoint:** `https://76ckmapns1.execute-api.us-east-1.amazonaws.com`

### 2. Open the Dashboard

Simply open `index.html` in your web browser:

```bash
open dashboard/index.html
```

Or on Linux:
```bash
xdg-open dashboard/index.html
```

### 3. Configure the API Endpoint

1. When the dashboard opens, you'll see an input field in the header
2. Paste your API endpoint URL
3. Click "Save"
4. The dashboard will immediately load your incident data

## Dashboard Sections

### Statistics Overview
- **Total Incidents**: All-time incident count
- **Last 24 Hours**: Recent activity
- **Auto-Remediation Eligible**: Incidents that can be auto-fixed
- **Average Severity**: Overall system health indicator

### Dashboard Tab
- Severity breakdown chart
- Recent incidents list
- Top error tags

### All Incidents Tab
- Complete incident list with filtering
- Filter by severity (ALL, CRITICAL, HIGH, MEDIUM, LOW)
- Click any incident to see full details including:
  - Summary and root cause analysis
  - Suggested remediation steps
  - Raw log messages
  - Tags and metadata

## API Endpoints

The dashboard uses these API endpoints:

- `GET /statistics` - System-wide statistics
- `GET /incidents?limit=50&severity=HIGH` - List incidents with optional filters
- `GET /incidents/{id}` - Get detailed incident information

## Hosting Options

### Option 1: Local File (Current Setup)
Just open `index.html` in your browser. No server needed!

### Option 2: S3 Static Website
Host the dashboard on S3 for team access:

```bash
# Create S3 bucket
aws s3 mb s3://rcra-dashboard-yourcompany

# Enable static website hosting
aws s3 website s3://rcra-dashboard-yourcompany \
  --index-document index.html

# Upload dashboard
aws s3 cp dashboard/index.html s3://rcra-dashboard-yourcompany/index.html \
  --acl public-read

# Access via:
# http://rcra-dashboard-yourcompany.s3-website-us-east-1.amazonaws.com
```

### Option 3: CloudFront Distribution
Add HTTPS and custom domain:

```bash
# Create CloudFront distribution pointing to your S3 bucket
# Add custom domain via Route 53
```

## Customization

### Change Refresh Interval
Edit `index.html`, line ~300:

```javascript
const interval = setInterval(fetchData, 60000); // 60000ms = 1 minute
```

### Modify Severity Colors
Edit the CSS section (lines 150-180):

```css
.severity-CRITICAL {
    background: #ff4444;  /* Change to your preferred color */
    color: white;
}
```

### Add Custom Filters
Extend the filter bar in the `IncidentsTab` component.

## Troubleshooting

### "Error: Failed to fetch"
- Check that your API endpoint URL is correct
- Ensure CORS is enabled on API Gateway (already configured)
- Verify the Lambda function has DynamoDB read permissions

### "No incidents found"
- Make sure you've triggered some errors in your monitored log groups
- Check that the Step Functions workflow has completed successfully
- Verify data exists in DynamoDB:
  ```bash
  aws dynamodb scan --table-name RCRARootCauseTable --max-items 5
  ```

### API Returns Empty Data
- The Lambda might not have permissions to read DynamoDB
- Check Lambda logs:
  ```bash
  aws logs tail /aws/lambda/rcra-dashboard-api --follow
  ```

## Screenshots

![Dashboard Overview](screenshots/overview.png)
![Incident Details](screenshots/details.png)

## Technology Stack

- **Frontend**: React 18 (via CDN - no build process!)
- **Styling**: Pure CSS with modern gradients and animations
- **Backend**: AWS Lambda + Python 3.12
- **API**: Amazon API Gateway (HTTP API)
- **Database**: Amazon DynamoDB

## Future Enhancements

- [ ] Export incidents to CSV/JSON
- [ ] Email notifications from dashboard
- [ ] Incident assignment and workflows
- [ ] Integration with Slack/Teams
- [ ] Custom dashboard themes
- [ ] Advanced filtering and search
- [ ] Incident comparison view
- [ ] Time-series charts

## Support

For issues or questions:
1. Check Lambda logs: `/aws/lambda/rcra-dashboard-api`
2. Verify API Gateway is deployed correctly
3. Test API endpoints with curl
4. Review browser console for JavaScript errors

## License

MIT License - See main project LICENSE file







