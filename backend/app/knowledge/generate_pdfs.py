import os
import sys
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def create_pdf(filename, title, content_sections):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        alignment=TA_LEFT,
        spaceAfter=20,
        textColor='#5B21B6' # Purple theme color
    )
    
    h2_style = ParagraphStyle(
        'DocSub',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
        textColor='#1E3A8A' # Blue accent
    )
    
    h3_style = ParagraphStyle(
        'DocSub2',
        parent=styles['Heading3'],
        fontSize=11,
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
        textColor='#475569'
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        spaceAfter=8,
        textColor='#1E293B'
    )
    
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    for section in content_sections:
        sec_type = section.get('type', 'body')
        text = section.get('text', '')
        if sec_type == 'h2':
            story.append(Paragraph(text, h2_style))
        elif sec_type == 'h3':
            story.append(Paragraph(text, h3_style))
        elif sec_type == 'body':
            story.append(Paragraph(text, body_style))
        elif sec_type == 'spacer':
            story.append(Spacer(1, section.get('height', 8)))
        elif sec_type == 'page_break':
            story.append(PageBreak())
            
    doc.build(story)
    print(f"Generated PDF: {filename}")

def main():
    docs_dir = r"c:\Users\User\Desktop\python\capstone_project\knowledge\docs"
    
    # Clean up existing directory and files
    if os.path.exists(docs_dir):
        print(f"Cleaning up existing knowledge docs in {docs_dir}...")
        for f in os.listdir(docs_dir):
            path = os.path.join(docs_dir, f)
            if os.path.isfile(path):
                os.remove(path)
    else:
        os.makedirs(docs_dir, exist_ok=True)
        
    # Define Content for all 9 documents
    
    # 1. faq.pdf
    create_pdf(
        os.path.join(docs_dir, "faq.pdf"),
        "ResolveDesk AI — Frequently Asked Questions (FAQ)",
        [
            {"type": "h2", "text": "Account Management"},
            {"type": "h3", "text": "How do I change my password?"},
            {"type": "body", "text": "You can change your password by navigating to User Settings > Security > Change Password. Fill in your current password and define a new one. Remember that passwords must be at least 10 characters long and contain both letters and numbers."},
            {"type": "h3", "text": "Can I delete my account?"},
            {"type": "body", "text": "To delete your account permanently, please contact our support team at support@resolvedesk.ai. For security reasons, deletion requests must be processed manually by an administrator."},
            {"type": "h2", "text": "Workspace & Board Configuration"},
            {"type": "h3", "text": "How do I create a new project board?"},
            {"type": "body", "text": "To create a new board, click the '+' button in the top navigation panel, select Create Board, enter a project title, and select a visibility level (Private, Shared, or Organization-wide)."},
            {"type": "h3", "text": "Can I import tasks from Trello or Jira?"},
            {"type": "body", "text": "Yes! ResolveDesk AI supports direct CSV imports or integrations with Jira and Trello. Navigate to Workspace Settings > Integrations, authorize your external provider, and follow the import wizard instructions."},
            {"type": "h2", "text": "Integrations"},
            {"type": "h3", "text": "How do I set up the Slack integration?"},
            {"type": "body", "text": "1. Navigate to Workspace Settings > Integrations.<br/>2. Click Add to Slack next to the Slack logo.<br/>3. Authorize the ResolveDesk bot in your Slack workspace.<br/>4. Set up notifications using commands (e.g. /resolvedesk subscribe #channel)."},
            {"type": "page_break"},
            {"type": "h2", "text": "Advanced FAQ & Workspace Sharing"},
            {"type": "h3", "text": "How do I share a workspace board with an external client?"},
            {"type": "body", "text": "To share a board externally, navigate to Board Settings > Access Control. Click 'Invite Member', enter the email address of the external client, and set their permission level to 'Viewer' or 'Guest'. Guest users will only have access to that specific board and cannot see the broader workspace directories. Guest limits apply depending on your plan details."},
            {"type": "h3", "text": "How is billing handled for added seats?"},
            {"type": "body", "text": "If you add new members to your workspace mid-cycle, ResolveDesk will dynamically calculate the proration amount for the remaining portion of that billing month. The cost for the new seats will appear as a prorated charge on your next monthly statement, ensuring you only pay for active periods."}
        ]
    )
    
    # 2. pricing_guide.pdf
    create_pdf(
        os.path.join(docs_dir, "pricing_guide.pdf"),
        "ResolveDesk AI — Pricing Packages Guide",
        [
            {"type": "h2", "text": "Subscription Plans Details"},
            {"type": "h3", "text": "Basic Plan"},
            {"type": "body", "text": "Price: $10 per user per month (billed monthly).<br/>Key Features:<br/>- Up to 5 project boards.<br/>- Standard kanban and list views.<br/>- 10 GB workspace storage.<br/>- Email support within 24 hours.<br/>Target Audience: Solopreneurs and small teams."},
            {"type": "h3", "text": "Pro Plan"},
            {"type": "body", "text": "Price: $20 per user per month (billed monthly).<br/>Key Features:<br/>- Unlimited project boards.<br/>- Gantt charts, Timeline, and Calendar views.<br/>- 100 GB workspace storage.<br/>- Priority support within 4 hours.<br/>- Advanced integrations (Slack, Github, Jira, Figma).<br/>Target Audience: Growing teams requiring timelines and advanced features."},
            {"type": "h3", "text": "Enterprise Plan"},
            {"type": "body", "text": "Price: Custom pricing (billed annually under a contract agreement).<br/>Key Features:<br/>- All Pro plan features.<br/>- Unlimited storage.<br/>- Dedicated Account Manager.<br/>- SSO / SAML authentication.<br/>- Custom API rate limits.<br/>- 99.9% uptime SLA.<br/>Target Audience: Larger organizations requiring security audits and high performance SLAs."},
            {"type": "page_break"},
            {"type": "h2", "text": "Pricing Add-ons and Billing Cycles Details"},
            {"type": "h3", "text": "Extra Workspace Storage Add-on"},
            {"type": "body", "text": "If your team exceeds the storage limit allocated in your subscription plan, you can purchase additional storage blocks. Storage is sold in increments of 50 GB for $5 per month. Navigate to Billing > Add-ons to upgrade storage limits immediately."},
            {"type": "h3", "text": "Workspace Guest Pass Policies"},
            {"type": "body", "text": "Basic plans do not support external guest invites. Pro plan users can invite up to 5 read-only guest viewers for free. Enterprise plans allow unlimited read-only guest passes under custom safety conditions. Guests with write permissions are billed as full active seats."}
        ]
    )
    
    # 3. refund_policy.pdf
    create_pdf(
        os.path.join(docs_dir, "refund_policy.pdf"),
        "ResolveDesk AI — Official Refund Policy",
        [
            {"type": "h2", "text": "Refund Terms & Conditions"},
            {"type": "h3", "text": "Annual Subscriptions"},
            {"type": "body", "text": "Eligibility: Users who purchase an Annual subscription are eligible for a full (100%) refund within 14 days of the initial transaction date."},
            {"type": "body", "text": "Process: Refund requests must be submitted to support. Once approved by our team, the refund is processed immediately, and funds will typically appear in your account within 5-10 business days."},
            {"type": "body", "text": "Late Requests: Requests submitted after the 14-day window are strictly ineligible for refunds. The subscription will remain active until the end of the current billing cycle."},
            {"type": "h3", "text": "Monthly Subscriptions"},
            {"type": "body", "text": "Eligibility: All Monthly plans are strictly non-refundable."},
            {"type": "body", "text": "Cancellations: When you cancel a monthly subscription, you will not receive a refund for the current billing month. You will continue to have access to the platform services until the end of the current monthly billing period."},
            {"type": "h3", "text": "Exceptional Cases"},
            {"type": "body", "text": "Under extreme conditions (e.g. system outages exceeding 24 hours or duplicate charges), customer success leads can authorize partial or full manual refunds on monthly plans as an escalation gesture."},
            {"type": "page_break"},
            {"type": "h2", "text": "Refund Process & Proration Details"},
            {"type": "h3", "text": "Initiating a Refund Request"},
            {"type": "body", "text": "All refund requests must be submitted directly through the client console (Billing > Refund Request) or via email to billing@resolvedesk.ai. To evaluate the refund, the billing manager checks the registration logs, subscription start dates, and previous renewal transactions in our support system. The customer's details must match the ID logged in our records."},
            {"type": "h3", "text": "Proration Calculation Guidelines"},
            {"type": "body", "text": "For plan upgrades, proration is handled automatically by adjusting the balance on the next invoice statement. Refund calculations for exceptional manual cancellations are based on the remaining days left in the current cycle, divided by the total billing period length."}
        ]
    )
    
    # 4. subscription_guide.pdf
    create_pdf(
        os.path.join(docs_dir, "subscription_guide.pdf"),
        "ResolveDesk AI — Subscription Management Guide",
        [
            {"type": "h2", "text": "Subscription Operations"},
            {"type": "h3", "text": "Upgrading your Plan"},
            {"type": "body", "text": "You can upgrade your subscription from Basic to Pro at any time:<br/>1. Navigate to Billing > Plan Details.<br/>2. Click Upgrade to Pro.<br/>3. Confirm seat allocation and payment details.<br/>4. Your account is upgraded immediately, and your current cycle is prorated."},
            {"type": "h3", "text": "Downgrading your Plan"},
            {"type": "body", "text": "To downgrade from Pro to Basic:<br/>1. Navigate to Billing > Plan Details.<br/>2. Click Downgrade to Basic.<br/>3. Choose to complete the downgrade at the end of the current billing cycle. Note: Ensure your workspace complies with Basic plan limits (e.g. up to 5 boards) before the cycle ends to avoid data lockouts."},
            {"type": "h3", "text": "Self-Service Cancellations"},
            {"type": "body", "text": "You can cancel your subscription renewal directly from the dashboard:<br/>1. Navigate to Billing > Settings.<br/>2. Click Cancel Renewal.<br/>3. Provide feedback and confirm.<br/>4. Your renewal status will be set to 'Cancelled', and billing will stop on your next renewal date."},
            {"type": "page_break"},
            {"type": "h2", "text": "Advanced Subscription Billing Cycle Configurations"},
            {"type": "h3", "text": "Aligning Multi-Workspace Invoices"},
            {"type": "body", "text": "If you manage multiple workspaces under a single user organization account, you can consolidate all workspace invoices into a single monthly billing statement. Access User Settings > Organization > Billing Consolidations to select the parent payment card and sync the billing dates of all child workspaces."},
            {"type": "h3", "text": "Payment Method Grace Periods"},
            {"type": "body", "text": "If a renewal charge fails, our system automatically grants a 7-day grace period. During this period, the account remains fully functional. Standard notifications are emailed to billing coordinators. If the card details are not updated within 7 days, the workspace will transition to read-only state."}
        ]
    )
    
    # 5. user_manual.pdf
    create_pdf(
        os.path.join(docs_dir, "user_manual.pdf"),
        "ResolveDesk AI — Platform User Manual",
        [
            {"type": "h2", "text": "Core Features & Navigation"},
            {"type": "h3", "text": "Workspace Board Views"},
            {"type": "body", "text": "ResolveDesk supports three primary views:<br/>1. Kanban Board: Drag-and-drop tasks across columns (To Do, In Progress, Review, Done).<br/>2. List View: A spreadsheet-style tabular list ideal for editing multiple tasks at once.<br/>3. Gantt Timeline: A timeline chart showing roadmaps, task durations, and milestones."},
            {"type": "h3", "text": "Task Management"},
            {"type": "body", "text": "Creating Tasks: Click '+ Add Task' in any column, enter a task name, and press Enter.<br/>Assignees & Dates: Double-click a card to assign team members, set dates, and attach priority tags (Low, Medium, High).<br/>Dependencies: In Gantt view, click and drag the connector line from the end of one task block to another to enforce execution order.<br/>Checklists: Break down large tasks into smaller items. Expand a task detail pane and add checklist rows."},
            {"type": "page_break"},
            {"type": "h2", "text": "Advanced Features & Task Automations"},
            {"type": "h3", "text": "Enabling Automated Task Rules"},
            {"type": "body", "text": "Users can build lightweight rule automations to reduce manual coordination clicks. Navigate to Board Settings > Automations > Rules. Click 'Create Rule' to specify triggers (e.g., 'When task moves to Done') and matching outcomes (e.g., 'Mark checklist complete and assign to Project Owner'). Rules are limited based on your subscription tier."},
            {"type": "h3", "text": "Exporting Workspace Data formats"},
            {"type": "body", "text": "Project data can be exported at any time. Click Workspace Settings > Export Data. Select from JSON format, CSV format, or PDF reports format. Workspace files and images are exported as a consolidated ZIP package."}
        ]
    )
    
    # 6. troubleshooting_guide.pdf
    create_pdf(
        os.path.join(docs_dir, "troubleshooting_guide.pdf"),
        "ResolveDesk AI — Technical Troubleshooting Guide",
        [
            {"type": "h2", "text": "Common Issues & Resolutions"},
            {"type": "h3", "text": "Browser Caching & Page Loading Errors"},
            {"type": "body", "text": "If UI elements fail to load or display stale content:<br/>1. Reload the page using a hard refresh (Ctrl + F5 on Windows, Cmd + Shift + R on Mac).<br/>2. Clear browser cookies and cache under Settings > Privacy > Clear Browsing Data."},
            {"type": "h3", "text": "WebSocket Connection Disconnects"},
            {"type": "body", "text": "ResolveDesk uses WebSockets to sync board updates in real time. If you see a 'Disconnected from server' warning:<br/>1. Check your internet connection status.<br/>2. Disable active VPNs or proxy servers that may block standard WebSockets.<br/>3. Refresh the page to trigger automatic socket reconnection."},
            {"type": "h3", "text": "Browser Compatibility"},
            {"type": "body", "text": "Ensure your browser is updated. We fully support Chrome (v100+), Firefox (v100+), Safari (v15+), and Edge (v100+). We do not support legacy Internet Explorer or old browser builds."},
            {"type": "page_break"},
            {"type": "h2", "text": "SSO and Advanced SSO Failure Resolutions"},
            {"type": "h3", "text": "Resolving SAML / SSO Login Loop Errors"},
            {"type": "body", "text": "If your team is redirected back to the login page repeatedly during single sign-on authentication:<br/>1. Contact your system admin to verify that the SAML certificate in Okta or Azure AD matches the metadata stored in ResolveDesk.<br/>2. Clear the browser cookie storage cache for 'resolvedesk.ai' and try logging in again.<br/>3. Use the backup SSO emergency URL provided during enterprise setup to bypass okta loops."},
            {"type": "h3", "text": "File Attachment Upload Failures"},
            {"type": "body", "text": "If task file uploads return error code 413, check that the file size is under the 25 MB limit for standard attachments. Verify that you have sufficient storage remaining in your workspace quota (Billing > Storage Limits)."}
        ]
    )
    
    # 7. api_documentation.pdf
    create_pdf(
        os.path.join(docs_dir, "api_documentation.pdf"),
        "ResolveDesk AI — REST API Documentation",
        [
            {"type": "h2", "text": "Developer API Specifications"},
            {"type": "h3", "text": "Authentication"},
            {"type": "body", "text": "All API requests must include a Bearer token in the headers:<br/>Authorization: Bearer <YOUR_API_KEY><br/>Generate API keys under User Settings > Developer Options > API Keys."},
            {"type": "h3", "text": "Base URL"},
            {"type": "body", "text": "https://api.resolvedesk.ai/v1"},
            {"type": "h3", "text": "Primary Endpoints"},
            {"type": "body", "text": "1. Projects:<br/>- List Projects: GET /projects<br/>- Create Project: POST /projects (payload: {'name': 'Project Name', 'visibility': 'private'})<br/>2. Tasks:<br/>- Get Project Tasks: GET /projects/{project_id}/tasks<br/>- Create Task: POST /projects/{project_id}/tasks (payload: {'title': 'Task Title', 'priority': 'high'})"},
            {"type": "h3", "text": "Rate Limiting"},
            {"type": "body", "text": "Basic: 100 requests per minute per key.<br/>Pro: 1,000 requests per minute per key.<br/>Enterprise: Custom contract rates.<br/>Exceeding limits will return HTTP code 429 Too Many Requests."},
            {"type": "page_break"},
            {"type": "h2", "text": "Developer Webhooks and Payload Specifications"},
            {"type": "h3", "text": "Registering Webhooks"},
            {"type": "body", "text": "Register webhooks from the developer portal console (POST /webhooks) to receive real-time updates when tasks are edited or created. Payloads are sent as JSON via POST with a signature key in headers (X-ResolveDesk-Signature) to verify payload authenticity. Webhook responses must return HTTP 200 within 5 seconds to avoid retries."},
            {"type": "h3", "text": "Sample Task Webhook JSON Payload"},
            {"type": "body", "text": "JSON schema structure:<br/>{ 'event': 'task.updated', 'timestamp': '2026-07-14T00:00:00Z', 'data': { 'task_id': 'tsk_002', 'title': 'Updated Title', 'assignee': 'cust_001', 'status': 'Done' } }"}
        ]
    )
    
    # 8. privacy_policy.pdf
    create_pdf(
        os.path.join(docs_dir, "privacy_policy.pdf"),
        "ResolveDesk AI — Privacy Policy",
        [
            {"type": "h2", "text": "Data Protection & Privacy Rules"},
            {"type": "h3", "text": "Compliance Scope"},
            {"type": "body", "text": "ResolveDesk AI is fully compliant with GDPR (General Data Protection Regulation) and CCPA (California Consumer Privacy Act) standards to ensure user safety and rights control."},
            {"type": "h3", "text": "PII Protection & Encryption"},
            {"type": "body", "text": "All personally identifiable information (PII) including email addresses, phone numbers, and names is encrypted in transit using TLS 1.3 and at rest using AES-256 encryption. We enforce automated redaction scripts to clear PII logs before exposing metrics to third-party dashboards."},
            {"type": "h3", "text": "Data Retention"},
            {"type": "body", "text": "Workspace data, board histories, and checklists are retained until user account deletion. Deleted workspace accounts have their data completely scrubbed from active storage databases within 30 days of deletion approval."},
            {"type": "page_break"},
            {"type": "h2", "text": "Subprocessors and GDPR Rights Process details"},
            {"type": "h3", "text": "Authorized Third-Party Subprocessors"},
            {"type": "body", "text": "ResolveDesk utilizes standard infrastructure providers to operate the software. This includes Amazon Web Services for database storage, Qdrant Cloud for vector index search services, and Stripe for billing and card transaction processing. Each subprocessor is audited annually to ensure safety."},
            {"type": "h3", "text": "Submitting a GDPR Data Erasure Request"},
            {"type": "body", "text": "Under GDPR regulations, users have the right to request deletion of all personal history details. Submit requests to privacy@resolvedesk.ai. Our team will verify credentials, fetch database records matching your email ID, and scrub all traces within 30 days."}
        ]
    )
    
    # 9. terms_and_conditions.pdf
    create_pdf(
        os.path.join(docs_dir, "terms_and_conditions.pdf"),
        "ResolveDesk AI — Terms and Conditions",
        [
            {"type": "h2", "text": "Terms of Service Agreement"},
            {"type": "h3", "text": "Account Creation"},
            {"type": "body", "text": "Users must register with valid email coordinates and maintain confidential credentials. ResolveDesk AI is not liable for data loss from unauthorized access resulting from compromised account keys."},
            {"type": "h3", "text": "Acceptable Use Policy"},
            {"type": "body", "text": "The platform may only be used for standard team coordination, project management, and related business communications. Prohibited acts include spreading malware, conducting unauthorized security scans, or loading prompt injection commands designed to degrade services."},
            {"type": "h3", "text": "Limitation of Liability"},
            {"type": "body", "text": "ResolveDesk AI is provided on an 'as-is' basis. Under no circumstances is ResolveDesk AI liable for lost revenues, business interruptions, or data damages exceeding the total amount paid by the customer to ResolveDesk AI in the preceding 12 months."},
            {"type": "page_break"},
            {"type": "h2", "text": "Governing Law and Dispute Resolution details"},
            {"type": "h3", "text": "Applicable Jurisdiction"},
            {"type": "body", "text": "These terms and conditions are governed by and construed in accordance with the laws of the State of California, without regard to its conflict of law principles. Any legal actions or proceedings must be initiated in state or federal courts located in San Francisco County, California."},
            {"type": "h3", "text": "Binding Arbitration details"},
            {"type": "body", "text": "Any disputes arising from this agreement will be resolved through binding arbitration administered by the American Arbitration Association in accordance with its Commercial Arbitration Rules, rather than class actions in court."}
        ]
    )

    print("Successfully generated all 2-page documents.")

if __name__ == '__main__':
    main()
