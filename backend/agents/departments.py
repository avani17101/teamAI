"""
Department definitions - system prompts, colors, icons, and sample transcripts.
Each department has specialized context for extraction and Q&A.
"""
import sqlite3
import os

DEPARTMENTS = {
    "engineering": {
        "id": "engineering",
        "name": "Engineering",
        "icon": "⚙️",
        "color": "#3b82f6",
        "description": "Software development, infrastructure, technical operations",
        "extraction_context": """Focus on:
- Technical tasks: code reviews, deployments, bug fixes, feature development
- Sprint commitments and story points
- Technical debt and blockers
- Infrastructure and DevOps tasks
- Code ownership and review assignments""",
        "query_context": """You are the Engineering Department AI. You understand:
- Software development lifecycle, sprints, CI/CD
- Code reviews, technical debt, deployment pipelines
- Team velocity and technical blockers
- System architecture decisions""",
        "sample_transcript": """[Sprint 14 Planning - Engineering Team | Feb 15, 2:00 PM]

[David Chen, Team Lead]
Alright everyone, let's get started. Quick round-robin on what we're committing to this sprint. Ahmed, you're up first.

[Ahmed Hassan, Backend Engineer]
Yeah so, um, I'm gonna finish that REST API refactoring by Wednesday. Should be straightforward. But actually, there's something more urgent - the auth service has a memory leak that's affecting prod right now. Like, users are getting logged out randomly. I need to prioritize fixing that first.

[David]
Okay that's definitely high priority. Do that first, then the refactoring. Priya, what about you?

[Priya Sharma, Frontend Engineer]
I'm taking the dashboard redesign. Probably 3 days of work? But I'm blocked waiting for Ahmed's new API spec. Can't really start until that's ready.

[Ahmed]
Yeah I'll get you that by tomorrow after I knock out this memory leak.

[Marcus Wilson, DevOps]
I've got setting up the staging environment for the new microservice. Should have it done by Friday. Heads up though - our K8s cluster is at 85% capacity. We're gonna need to scale up before the next deployment or we'll run into issues.

[David]
Good catch. Add that to your tasks. Lisa, QA?

[Lisa Park, QA Engineer]
I'm doing test automation for the payment flow. But, uh, I need access to the sandbox environment and IT hasn't provisioned it yet. So I'm blocked until that's set up.

[David]
I'll ping IT today. Alright, bigger decision - we've been discussing moving the payment module from monolithic to microservices architecture. I think we should pull the trigger on this. It'll impact our Q2 roadmap but it's the right call long-term.

[Team murmurs agreement]

[Priya]
One thing - no one's assigned to that security audit that's due before launch on March 20th. That's like, 5 weeks away. We need someone on that.

[David]
You're right. I'll assign that next standup. Okay, sprint demo is Friday 3pm. See you all tomorrow.

[Meeting ends 2:47 PM]""",
    },

    "hr": {
        "id": "hr",
        "name": "HR",
        "icon": "👥",
        "color": "#8b5cf6",
        "description": "People operations, hiring, performance, team welfare",
        "extraction_context": """Focus on:
- Hiring tasks: job postings, interview scheduling, offer letters
- Onboarding and offboarding processes
- Performance review timelines and owners
- Policy updates and compliance
- Employee welfare initiatives
- Team building and culture activities""",
        "query_context": """You are the HR Department AI. You understand:
- Recruitment pipelines and hiring processes
- Performance management and review cycles
- Employee relations and wellbeing
- HR compliance, policies, and legal requirements
- Onboarding/offboarding workflows""",
        "sample_transcript": """[HR Monthly Sync | Feb 10, 9:00 AM]

[Fatima Al-Hassan, HR Director]
Morning team. Let's start with recruitment. Khalid, what's the status on our open positions?

[Khalid Ibrahim, Talent Acquisition]
We've got 3 open roles - one Senior ML Engineer and two Data Scientists. I'm leading the screening for the ML Engineer position. First round interviews are scheduled for next week. But heads up - two of our top candidates have competing offers that expire this Friday, so we need to move fast on those.

[Fatima]
Okay, let's prioritize that. I'll expedite approvals if needed. Sara, onboarding update?

[Sara Khalil, HR Coordinator]
Omar Saeed starts Monday. I need to have his onboarding pack and system access ready by Friday. IT access request was submitted yesterday, so... fingers crossed they process it in time.

[Fatima]
Follow up with IT if you don't hear back by tomorrow. Moving on - performance reviews. How are we tracking?

[Rania Mustafa, HR Manager]
Q1 reviews are due March 1st. We sent the system access to all managers last week. Problem is, only like 40% have even started their reviews. We're way behind schedule. I'm planning to send reminder emails this week.

[Fatima]
Please do that today, not later this week. We can't afford to slip on this. Policy updates?

[Rania]
Yeah, the remote work policy got updated - employees can now work remotely 3 days per week instead of 2. I'll send an announcement to everyone by Wednesday and update the employee handbook on the portal.

[Layla Hassan, Wellbeing Coordinator]
Quick update - Mental Health Awareness Month is coming up in March. I'm organizing a workshop series. Budget request was approved for 5,000 dirhams.

[Fatima]
Great work, Layla. Now, bigger topic - we've been discussing moving away from our spreadsheet-based recruitment process to a proper platform. I think it's time we make the switch to Greenhouse. Ahmed from IT will lead the technical setup. Everyone agreed?

[Team agrees]

[Fatima]
Done. Last thing, and this stays confidential - based on recent 1-on-1s, we've identified two senior engineers who are flight risks. I've escalated this to their department heads. Let's keep an eye on that situation.

[Meeting ends 9:42 AM]""",
    },

    "marcom": {
        "id": "marcom",
        "name": "Marketing & Comms",
        "icon": "📣",
        "color": "#f59e0b",
        "description": "Marketing campaigns, communications, brand, events",
        "extraction_context": """Focus on:
- Campaign launches: deadlines, channels, budgets, owners
- Content creation: blog posts, social media, press releases
- Event planning: conferences, webinars, launch events
- Brand and messaging decisions
- Analytics and reporting tasks
- Partner and media relations""",
        "query_context": """You are the Marketing & Communications Department AI. You understand:
- Campaign planning and execution timelines
- Content calendars and editorial processes
- Event management and logistics
- Brand guidelines and messaging
- Digital marketing: SEO, social, email, paid
- PR and media relations""",
        "sample_transcript": """[MarCom Weekly Standup | Feb 12, 11:00 AM]

[Nour Khalil, MarCom Director]
Hey everyone, let's make this quick. Zainab, start us off with the Q1 campaign.

[Zainab Amir, Creative Lead]
So the "Future of AI" campaign goes live March 10th. All the creative assets are due to design by Feb 28th - that's in like 16 days. Copy review with legal is tomorrow. Budget-wise, we've spent $32K out of our $50K allocation, so we're in good shape there.

[Nour]
Perfect. Tariq, social media?

[Tariq Hassan, Social Media Manager]
Yeah, uh, the Instagram and LinkedIn content calendar for March needs to be locked by Monday. I'm owning that. But just FYI - we're behind on thought leadership posts. We published 2 in February when we planned for 8. That's... not great.

[Nour]
Let's talk offline about what went wrong there. Hassan, website?

[Hassan Mahmoud, Web Developer]
The new product landing page needs to be live by March 5th. I'm building it, but I'm blocked waiting on final product screenshots from the product team. Can't really finish without those.

[Nour]
I'll escalate that today. Nadia, press release?

[Nadia Rashid, PR Manager]
PR is written and ready to go. I'll distribute to the press list on March 8th. Just need the CEO quote approved - hopefully by tomorrow.

[Lina Saeed, Events Coordinator]
And for the webinar on March 20th - registration page needs to go live this week. I've got 3 speakers confirmed, waiting on confirmation from the fourth one.

[Nour]
Good. Alright, tough decision time. We've been running the podcast series, but with current resource constraints, I think we need to pause it until Q3. I know that's not ideal, but we're spread too thin. Everyone aligned on that?

[Team murmurs agreement]

[Nour]
Okay, it's decided. One big risk to flag - Hassan's blocked on product screenshots. If the product team misses their deadline, our whole launch campaign is at risk. I'm treating this as a blocker and escalating to their director today.

[Meeting ends 11:28 AM]""",
    },

    "innovation": {
        "id": "innovation",
        "name": "Industry Innovation",
        "icon": "🚀",
        "color": "#22c55e",
        "description": "Research partnerships, product innovation, emerging tech",
        "extraction_context": """Focus on:
- Research milestones: paper submissions, dataset releases, model evaluations
- Industry partnerships: MoUs, pilots, joint projects
- Grant applications and funding deadlines
- Innovation lab experiments and prototypes
- IP and patent filing tasks
- Conference submissions and presentations""",
        "query_context": """You are the Industry Innovation Department AI. You understand:
- Research and development cycles
- Academic and industry partnerships
- Grant funding and research budgets
- Technology scouting and evaluation
- Pilot programs and proof-of-concepts
- IP management and commercialization""",
        "sample_transcript": """[Innovation Lab Weekly Sync | Feb 16, 10:00 AM]

[Prof. Ibrahim Al-Mansour, Lab Director]
Good morning everyone. Let's jump right in. Aisha, give us an update on the ACL submission.

[Dr. Aisha Rahman, Research Lead]
So... the deadline is March 15th, which gives us about 4 weeks. The paper itself is solid, but we still haven't finished the benchmark experiments. And here's the problem - I need GPU access on the cluster, but it's totally maxed out right now. Like 95% utilization. Another team is running their models 24/7.

[Ibrahim]
That's a blocker. I'll talk to IT today about expanding capacity or getting you priority access. Mohammed, what's happening with the TechCorp MoU?

[Mohammed Al-Hashimi, Partnerships]
Yeah, it's in final legal review. I'm following up with legal tomorrow to nail down the signing date. We're targeting end of month, so that's, like, two weeks from now.

[Ibrahim]
Good. Keep on them. Nadia, Sara - grant application?

[Dr. Nadia Khan, Research Scientist]
ADEK grant is due March 20th. I'm writing the technical proposal, Sara's doing the financials. We're asking for 2 million dirhams. Both parts should be done by next week, then we need to merge and review everything by March 17th.

[Sara Ahmed, Program Manager]
Yep, on track for that.

[Khalid Mansoor, DevOps]
Uh, quick thing - the Arabic Voice Dataset v2 is ready to go live, but IT security review is still pending. I'm assigned to that. Once we get sign-off, I can push it to HuggingFace immediately.

[Yusuf Ali, Engineering Lead]
And the Al Noor Hospital pilot starts April 1st. Integration testing kicks off next week. I'm leading that technical side.

[Ibrahim]
Perfect. One more thing - I think we should apply for the UNESCO AI Ethics grant. Dr. Hana, would you be willing to lead that application? It aligns perfectly with your research.

[Dr. Hana Said, Ethics Researcher]
Absolutely, I'd love to.

[Ibrahim]
Great. That's decided then. But we seriously need to address this GPU bottleneck. It's blocking multiple projects right now, not just Aisha's.

[Meeting ends 10:38 AM]""",
    },

    "sales": {
        "id": "sales",
        "name": "Sales",
        "icon": "💼",
        "color": "#ef4444",
        "description": "Sales operations, deals, client relationships, revenue",
        "extraction_context": """Focus on:
- Deal progress: pipeline stages, close dates, deal owners
- Client meetings and follow-ups
- Proposal deadlines and contract negotiations
- Sales targets and quotas
- CRM updates and data hygiene
- Customer onboarding tasks""",
        "query_context": """You are the Sales Department AI. You understand:
- Sales pipeline and opportunity management
- Client relationship stages and touch points
- Deal structures, pricing, and negotiations
- Sales forecasting and quota tracking
- CRM workflows and sales processes
- Customer success handoffs""",
        "sample_transcript": """[Sales Pipeline Review | Feb 14, 2:00 PM]

[Sarah Chen, Sales Director]
Alright team, pipeline review time. John, let's start with the big one - TechCorp.

[John Martinez, Enterprise AE]
TechCorp is $500K ARR, we're in final negotiations. Contract review is scheduled for Friday. Legal should have their redlines done by tomorrow. Big thing - we need CEO approval before Friday or this slips.

[Sarah]
I'll make sure the CEO has everything he needs. Lisa, how did this week go?

[Lisa Wong, SMB Account Executive]
Really good week actually. Closed 3 deals, $75K MRR total. I'm following up with 5 hot leads from last week's webinar. Got demos scheduled Monday and Wednesday.

[Sarah]
Love it. Mike, renewals?

[Mike O'Connor, Account Manager]
Q1 renewals are at 85% completion. I've got 4 at-risk accounts I need to connect with by end of week. DataCo especially - they mentioned budget cuts, so I flagged them as churn risk.

[Sarah]
Stay close to them. Amanda, proposals?

[Amanda Park, Solutions Engineer]
FinanceInc proposal is due March 5th. I'm writing it but I'm blocked - need updated pricing from the Product team. Can't submit without that.

[Sarah]
I'll ping Product today. Okay, we got 12 new demo requests from the conference. I'll distribute those across the team by tomorrow.

Now, bigger process change - we're implementing a new discount approval process. Any deal over $100K needs VP sign-off going forward. I know this might slow down some closes, but we need better margin control.

[Team discussing]

[John]
Makes sense, but can we expedite the approval workflow? Don't want deals dying in approval purgatory.

[Sarah]
Fair point. I'll set up a fast-track process. One risk I'm worried about - we've got three major deals all scheduled to close March 31st. That's end of quarter. If even one slips, we miss our targets. Everyone needs to be laser-focused on those.

[Meeting ends 2:36 PM]""",
    },

    "product": {
        "id": "product",
        "name": "Product",
        "icon": "🎨",
        "color": "#ec4899",
        "description": "Product strategy, roadmap, design, user research",
        "extraction_context": """Focus on:
- Feature specifications and PRDs
- User research and testing sessions
- Design reviews and mockup approvals
- Roadmap prioritization decisions
- Product launch checklists
- Metrics and analytics reviews
- Stakeholder alignment tasks""",
        "query_context": """You are the Product Department AI. You understand:
- Product development lifecycle and agile methodologies
- User research methods and design thinking
- Product roadmapping and prioritization frameworks
- Feature specification and requirements gathering
- Product metrics, KPIs, and A/B testing
- Cross-functional coordination (eng, design, marketing)""",
        "sample_transcript": """[Product Sprint Planning | Feb 13, 3:00 PM]

[Marcus Kim, Product Lead]
Hey team. Let's plan Q1 features. Emily, dashboard redesign?

[Emily Zhang, Product Manager]
The new analytics dashboard moves to development next sprint. Design is done. I'll have the PRD written by Wednesday. Engineering needs it by Friday to start estimation.

[Rachel Thompson, UX Researcher]
I'm coordinating 10 user interviews for the mobile app redesign. All sessions are scheduled for next week. I'll share insights with the design team by March 10th.

[Marcus]
Perfect. Big prioritization call - we need to decide whether to keep API integrations in Q1 or defer it.

[Team discusses]

[Marcus]
Okay, decision made - we're deferring API integrations to Q2. We need to focus on core dashboard improvements first. This impacts our roadmap presentation to execs though. I need to update that deck.

[James Liu, Product Analyst]
Quick win to share - the new onboarding flow A/B test results came in. We improved activation by 23%. That's huge. We should ship this to 100% of users next week. I'll coordinate with engineering on the rollout.

[Marcus]
Love that. Sarah, metrics?

[Sarah Patel, Data Analyst]
Monthly active users are up 15%, which is good. But engagement is totally flat. We need to dig into drop-off points. I'll analyze the funnel data and present findings on Friday.

[Alex Chen, Product Designer]
For the payment feature launch on March 15th - go/no-go meeting is March 12th. Marketing is asking for final screenshots by March 8th. I'm responsible for getting those to them.

[Marcus]
Great. One risk - the design team is completely overloaded right now. If the mobile mockups slip, that'll delay engineering's sprint planning. Let's keep a close eye on capacity.

[Meeting ends 3:41 PM]""",
    },
}


def _get_db_path():
    """Get database path."""
    return os.path.join(os.path.dirname(__file__), "..", "..", "data", "teamai.db")


def _get_db_departments() -> dict:
    """Get departments from database org_context table."""
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        return {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all departments from org_context
        cursor.execute("SELECT department, mission FROM org_context WHERE department IS NOT NULL")
        db_depts = {}

        for dept_id, mission in cursor.fetchall():
            # Skip if this is already a hardcoded department
            if dept_id in DEPARTMENTS:
                continue

            # Create dynamic department entry
            db_depts[dept_id] = {
                "id": dept_id,
                "name": dept_id.replace("-", " ").title(),
                "icon": "🏢",  # Default icon for custom departments
                "color": "#6c63ff",  # Default accent color
                "description": mission[:100] if mission else f"Custom {dept_id} department",
                "extraction_context": f"Focus on tasks, decisions, and risks relevant to {dept_id}.",
                "query_context": f"You are the {dept_id.title()} Department AI.",
                "sample_transcript": "No sample transcript available for custom departments.",
            }

        conn.close()
        return db_depts
    except Exception as e:
        print(f"[departments] Error loading db departments: {e}")
        return {}


def get_department(dept_id: str) -> dict:
    """Get department by ID, checking both hardcoded and database departments."""
    # First check hardcoded departments
    if dept_id in DEPARTMENTS:
        return DEPARTMENTS[dept_id]

    # Then check database departments
    db_depts = _get_db_departments()
    if dept_id in db_depts:
        return db_depts[dept_id]

    # Default to engineering if not found
    return DEPARTMENTS["engineering"]


def list_departments() -> list:
    """List all departments (hardcoded + database)."""
    # Start with hardcoded departments
    all_depts = {d["id"]: d for d in DEPARTMENTS.values()}

    # Add database departments (they won't override hardcoded ones due to skip logic in _get_db_departments)
    db_depts = _get_db_departments()
    for dept_id, dept_data in db_depts.items():
        all_depts[dept_id] = dept_data

    # Return as list
    return [
        {
            "id": d["id"],
            "name": d["name"],
            "icon": d["icon"],
            "color": d["color"],
            "description": d["description"],
        }
        for d in all_depts.values()
    ]
