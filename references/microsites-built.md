# Microsites built — reference list

**Check this list before building any new microsite so an existing one is not duplicated.**

Last updated: 2026-11-26. The built folders were removed from `projects/microsites/` to declutter the AIOS. This file is now the single source of truth for what has been built.

## Standing Beauty Booked Up CTA rule

Every Beauty Booked Up microsite and blog article built now or in future must link "Book a free call" to `https://www.supersaas.co.uk/schedule/beautybookedup/Consultation`. In HTML, open it in a new tab with `rel="noopener noreferrer"`.

- Full backup of all 60 local folders: `~/Downloads/webawesome-microsites/webawesome-all-microsites-full-backup.zip`
- Upload-ready zip for the 50 geo pages (index.html + og-image.png): `~/Downloads/webawesome-microsites/webawesome-50-microsites-upload.zip`
- Root sitemap URL blocks for the 50 geo pages: `~/Downloads/webawesome-microsites/webawesome-50-sitemap-urls.txt`
- Rebuild the 50 geo pages: `python3 scripts/generate-geo-microsites.py`
- Design reference kept in the repo: `scripts/templates/consulting/index.html`

## 1. WebAwesome — UK geo microsites (50)

Built locally from the consulting.zip design system. Each has unique local copy, a 1200x630 OG image, and a per-folder sitemap. As of 2026-11-20 these are **built locally, not published** — the upload zip is ready for cPanel.

| # | Page title | Live URL (canonical) | Local folder slug | Service | Region |
|---:|---|---|---|---|---|
| 1 | Digital consulting in Greater London \| WebAwesome | https://www.webawesome.co.uk/consulting-in-greater-london/ | `webawesome-consulting-greater-london` | Digital consulting | Greater London |
| 2 | AI automation in Greater Manchester \| WebAwesome | https://www.webawesome.co.uk/ai-in-greater-manchester/ | `webawesome-ai-greater-manchester` | AI automation | Greater Manchester |
| 3 | WordPress websites in West Midlands \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-west-midlands/ | `webawesome-wordpress-west-midlands` | WordPress websites | West Midlands |
| 4 | App design in Merseyside \| WebAwesome | https://www.webawesome.co.uk/apps-in-merseyside/ | `webawesome-apps-merseyside` | App design | Merseyside |
| 5 | AI automation in West Yorkshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-west-yorkshire/ | `webawesome-ai-west-yorkshire` | AI automation | West Yorkshire |
| 6 | App design in South Yorkshire \| WebAwesome | https://www.webawesome.co.uk/apps-in-south-yorkshire/ | `webawesome-apps-south-yorkshire` | App design | South Yorkshire |
| 7 | WordPress websites in Tyne and Wear \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-tyne-and-wear/ | `webawesome-wordpress-tyne-and-wear` | WordPress websites | Tyne and Wear |
| 8 | Digital consulting in Bristol \| WebAwesome | https://www.webawesome.co.uk/consulting-in-bristol/ | `webawesome-consulting-bristol` | Digital consulting | Bristol |
| 9 | AI automation in Hampshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-hampshire/ | `webawesome-ai-hampshire` | AI automation | Hampshire |
| 10 | WordPress websites in Kent \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-kent/ | `webawesome-wordpress-kent` | WordPress websites | Kent |
| 11 | Digital consulting in Essex \| WebAwesome | https://www.webawesome.co.uk/consulting-in-essex/ | `webawesome-consulting-essex` | Digital consulting | Essex |
| 12 | AI automation in Surrey \| WebAwesome | https://www.webawesome.co.uk/ai-in-surrey/ | `webawesome-ai-surrey` | AI automation | Surrey |
| 13 | WordPress websites in Norfolk \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-norfolk/ | `webawesome-wordpress-norfolk` | WordPress websites | Norfolk |
| 14 | App design in Oxfordshire \| WebAwesome | https://www.webawesome.co.uk/apps-in-oxfordshire/ | `webawesome-apps-oxfordshire` | App design | Oxfordshire |
| 15 | AI automation in Cambridgeshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-cambridgeshire/ | `webawesome-ai-cambridgeshire` | AI automation | Cambridgeshire |
| 16 | Digital consulting in Nottinghamshire \| WebAwesome | https://www.webawesome.co.uk/consulting-in-nottinghamshire/ | `webawesome-consulting-nottinghamshire` | Digital consulting | Nottinghamshire |
| 17 | WordPress websites in Devon \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-devon/ | `webawesome-wordpress-devon` | WordPress websites | Devon |
| 18 | Digital consulting in South Wales \| WebAwesome | https://www.webawesome.co.uk/consulting-in-south-wales/ | `webawesome-consulting-south-wales` | Digital consulting | South Wales |
| 19 | App design in Scotland's Central Belt \| WebAwesome | https://www.webawesome.co.uk/apps-in-central-belt-scotland/ | `webawesome-apps-central-belt-scotland` | App design | Scotland's Central Belt |
| 20 | AI automation in Northern Ireland \| WebAwesome | https://www.webawesome.co.uk/ai-in-northern-ireland/ | `webawesome-ai-northern-ireland` | AI automation | Northern Ireland |
| 21 | Digital consulting in North Yorkshire \| WebAwesome | https://www.webawesome.co.uk/consulting-in-north-yorkshire/ | `webawesome-consulting-north-yorkshire` | Digital consulting | North Yorkshire |
| 22 | WordPress websites in Lancashire \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-lancashire/ | `webawesome-wordpress-lancashire` | WordPress websites | Lancashire |
| 23 | AI automation in Cheshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-cheshire/ | `webawesome-ai-cheshire` | AI automation | Cheshire |
| 24 | App design in Derbyshire \| WebAwesome | https://www.webawesome.co.uk/apps-in-derbyshire/ | `webawesome-apps-derbyshire` | App design | Derbyshire |
| 25 | WordPress websites in Leicestershire \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-leicestershire/ | `webawesome-wordpress-leicestershire` | WordPress websites | Leicestershire |
| 26 | AI automation in Lincolnshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-lincolnshire/ | `webawesome-ai-lincolnshire` | AI automation | Lincolnshire |
| 27 | App design in Staffordshire \| WebAwesome | https://www.webawesome.co.uk/apps-in-staffordshire/ | `webawesome-apps-staffordshire` | App design | Staffordshire |
| 28 | Digital consulting in Warwickshire \| WebAwesome | https://www.webawesome.co.uk/consulting-in-warwickshire/ | `webawesome-consulting-warwickshire` | Digital consulting | Warwickshire |
| 29 | WordPress websites in Worcestershire \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-worcestershire/ | `webawesome-wordpress-worcestershire` | WordPress websites | Worcestershire |
| 30 | Digital consulting in Shropshire \| WebAwesome | https://www.webawesome.co.uk/consulting-in-shropshire/ | `webawesome-consulting-shropshire` | Digital consulting | Shropshire |
| 31 | AI automation in Gloucestershire \| WebAwesome | https://www.webawesome.co.uk/ai-in-gloucestershire/ | `webawesome-ai-gloucestershire` | AI automation | Gloucestershire |
| 32 | WordPress websites in Wiltshire \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-wiltshire/ | `webawesome-wordpress-wiltshire` | WordPress websites | Wiltshire |
| 33 | AI automation in Somerset \| WebAwesome | https://www.webawesome.co.uk/ai-in-somerset/ | `webawesome-ai-somerset` | AI automation | Somerset |
| 34 | WordPress websites in Dorset \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-dorset/ | `webawesome-wordpress-dorset` | WordPress websites | Dorset |
| 35 | Digital consulting in Cornwall \| WebAwesome | https://www.webawesome.co.uk/consulting-in-cornwall/ | `webawesome-consulting-cornwall` | Digital consulting | Cornwall |
| 36 | App design in East Sussex \| WebAwesome | https://www.webawesome.co.uk/apps-in-east-sussex/ | `webawesome-apps-east-sussex` | App design | East Sussex |
| 37 | AI automation in West Sussex \| WebAwesome | https://www.webawesome.co.uk/ai-in-west-sussex/ | `webawesome-ai-west-sussex` | AI automation | West Sussex |
| 38 | Digital consulting in Berkshire \| WebAwesome | https://www.webawesome.co.uk/consulting-in-berkshire/ | `webawesome-consulting-berkshire` | Digital consulting | Berkshire |
| 39 | WordPress websites in Buckinghamshire \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-buckinghamshire/ | `webawesome-wordpress-buckinghamshire` | WordPress websites | Buckinghamshire |
| 40 | AI automation in Hertfordshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-hertfordshire/ | `webawesome-ai-hertfordshire` | AI automation | Hertfordshire |
| 41 | App design in Bedfordshire \| WebAwesome | https://www.webawesome.co.uk/apps-in-bedfordshire/ | `webawesome-apps-bedfordshire` | App design | Bedfordshire |
| 42 | Digital consulting in Suffolk \| WebAwesome | https://www.webawesome.co.uk/consulting-in-suffolk/ | `webawesome-consulting-suffolk` | Digital consulting | Suffolk |
| 43 | AI automation in Northamptonshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-northamptonshire/ | `webawesome-ai-northamptonshire` | AI automation | Northamptonshire |
| 44 | App design in Cumbria \| WebAwesome | https://www.webawesome.co.uk/apps-in-cumbria/ | `webawesome-apps-cumbria` | App design | Cumbria |
| 45 | App design in County Durham \| WebAwesome | https://www.webawesome.co.uk/apps-in-county-durham/ | `webawesome-apps-county-durham` | App design | County Durham |
| 46 | Digital consulting in Northumberland \| WebAwesome | https://www.webawesome.co.uk/consulting-in-northumberland/ | `webawesome-consulting-northumberland` | Digital consulting | Northumberland |
| 47 | WordPress websites in Isle of Wight \| WebAwesome | https://www.webawesome.co.uk/wordpress-in-isle-of-wight/ | `webawesome-wordpress-isle-of-wight` | WordPress websites | Isle of Wight |
| 48 | AI automation in Herefordshire \| WebAwesome | https://www.webawesome.co.uk/ai-in-herefordshire/ | `webawesome-ai-herefordshire` | AI automation | Herefordshire |
| 49 | App design in North Wales \| WebAwesome | https://www.webawesome.co.uk/apps-in-north-wales/ | `webawesome-apps-north-wales` | App design | North Wales |
| 50 | Digital consulting in Scottish Highlands and Islands \| WebAwesome | https://www.webawesome.co.uk/consulting-in-highlands-and-islands-scotland/ | `webawesome-consulting-highlands-and-islands-scotland` | Digital consulting | Scottish Highlands and Islands |

## 2. Older local builds (10)

These were the original hand-written static microsites. Their live paths come from `scratchpad/seo_upgrade.py`. Content survives in the full backup and in `docs/backup/microsites/microsites/`.

| Local folder | Brand | Live URL | Title |
|---|---|---|---|
| `ai-automation-audit` | WebAwesome | https://www.webawesome.co.uk/ai-automation-audit/ | AI Automation Audit |
| `webawesome-consult` | WebAwesome | https://www.webawesome.co.uk/consult/ | Strategic Digital Consulting |
| `nowsorted-ai-audit` | Sorted | https://nowsorted.co.uk/ai-audit/ | AI Automation Audit |
| `nowsorted-career` | Sorted | https://nowsorted.co.uk/career/ | Career Change Strategy |
| `nowsorted-consult` | Sorted | https://nowsorted.co.uk/consult/ | Strategic Digital Consulting |
| `nowsorted-rota` | Sorted | https://nowsorted.co.uk/rota/ | Staff Rota Software |
| `mentoringba-career` | MentoringBA | https://mentoringba.org/career/ | Career Transition Strategy |
| `propertiesonthego-ai-audit` | PropertiesOnTheGo | https://propertiesonthego.com.ng/ai-audit/ | AI Automation Audit |
| `propertiesonthego-career` | PropertiesOnTheGo | https://propertiesonthego.com.ng/career/ | Career Change Strategy |
| `propertiesonthego-consult` | PropertiesOnTheGo | https://propertiesonthego.com.ng/consult/ | Strategic Digital Consulting |

## 3. Live WordPress microsites — WebAwesome (10)

No local build files; these exist only as WordPress pages. Source: `scripts/pyrunner/blog-drafter.py`.

| # | Live URL |
|---:|---|
| 1 | https://webawesome.co.uk/consulting/ |
| 2 | https://webawesome.co.uk/ai/ |
| 3 | https://webawesome.co.uk/apps/ |
| 4 | https://webawesome.co.uk/wordpress/ |
| 5 | https://webawesome.co.uk/discovery-call/ |
| 6 | https://webawesome.co.uk/aios/ |
| 7 | https://webawesome.co.uk/london-businesses/ |
| 8 | https://webawesome.co.uk/solutions-consulting/ |
| 9 | https://webawesome.co.uk/applications/ |
| 10 | https://webawesome.co.uk/app-design/ |

## 4. Live WordPress microsites — MentoringBA (10)

Source: `scripts/pyrunner/mentoringba-blog-poster.py`.

| # | Live URL |
|---:|---|
| 1 | https://www.mentoringba.org/coach/ |
| 2 | https://www.mentoringba.org/business-analyst/ |
| 3 | https://www.mentoringba.org/job-support/ |
| 4 | https://www.mentoringba.org/interview-ready/ |
| 5 | https://www.mentoringba.org/analyst/ |
| 6 | https://www.mentoringba.org/product-owner/ |
| 7 | https://www.mentoringba.org/ba-role/ |
| 8 | https://www.mentoringba.org/training/ |
| 9 | https://www.mentoringba.org/free-courses/ |
| 10 | https://www.mentoringba.org/level-up/ |

## 5. Live WordPress microsites — Best Homes Support (22)

Source: `scripts/pyrunner/bhs-blog-poster.py`. Do not imply service in unoperated boroughs.

| # | Live URL |
|---:|---|
| 1 | https://besthomesupport.uk/autism-support-london/ |
| 2 | https://besthomesupport.uk/care-areas-london/ |
| 3 | https://besthomesupport.uk/care-in-bexley/ |
| 4 | https://besthomesupport.uk/care-in-bromley/ |
| 5 | https://besthomesupport.uk/care-in-croydon/ |
| 6 | https://besthomesupport.uk/care-in-enfield/ |
| 7 | https://besthomesupport.uk/care-in-greenwich/ |
| 8 | https://besthomesupport.uk/care-in-lambeth/ |
| 9 | https://besthomesupport.uk/care-in-lewisham/ |
| 10 | https://besthomesupport.uk/care-in-southwark/ |
| 11 | https://besthomesupport.uk/care-in-tower-hamlets/ |
| 12 | https://besthomesupport.uk/care-jobs-london/ |
| 13 | https://besthomesupport.uk/care-packages-london/ |
| 14 | https://besthomesupport.uk/care-referrals-london/ |
| 15 | https://besthomesupport.uk/complex-care-london/ |
| 16 | https://besthomesupport.uk/home-care-london/ |
| 17 | https://besthomesupport.uk/how-to-arrange-care-london/ |
| 18 | https://besthomesupport.uk/learning-disability-support-london/ |
| 19 | https://besthomesupport.uk/live-in-care-london/ |
| 20 | https://besthomesupport.uk/mental-health-support-london/ |
| 21 | https://besthomesupport.uk/respite-care-london/ |
| 22 | https://besthomesupport.uk/supported-living-london/ |

## 6. Keyword campaign — 100 topic x sector pages (built 2026-11-20, NOT published)

Five weekly zips in `~/Downloads/webawesome-microsites/webawesome-keyword-campaign-week-{1..5}.zip`, 20 pages each. Mixes service/intent topic with business sector so each page has two dimensions of content. Generator: `scripts/generate-keyword-microsites.py`. Status: **built locally, not published**.

| # | Week | Page title | Live URL (canonical) |
|---:|---:|---|---|
| 1 | 1 | AI consulting for small businesses | WebAwesome | https://www.webawesome.co.uk/ai-consulting-for-small-business/ |
| 2 | 1 | AI consulting for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/ai-consulting-for-charities/ |
| 3 | 1 | AI consulting for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/ai-consulting-for-healthcare-education/ |
| 4 | 1 | AI consulting for professional services firms | WebAwesome | https://www.webawesome.co.uk/ai-consulting-for-professional-services/ |
| 5 | 1 | AI consulting for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/ai-consulting-for-trades-field-service/ |
| 6 | 1 | AI automation audit for small businesses | WebAwesome | https://www.webawesome.co.uk/ai-automation-audit-for-small-business/ |
| 7 | 1 | AI automation audit for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/ai-automation-audit-for-charities/ |
| 8 | 1 | AI automation audit for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/ai-automation-audit-for-healthcare-education/ |
| 9 | 1 | AI automation audit for professional services firms | WebAwesome | https://www.webawesome.co.uk/ai-automation-audit-for-professional-services/ |
| 10 | 1 | AI automation audit for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/ai-automation-audit-for-trades-field-service/ |
| 11 | 1 | AI readiness assessment for small businesses | WebAwesome | https://www.webawesome.co.uk/ai-readiness-assessment-for-small-business/ |
| 12 | 1 | AI readiness assessment for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/ai-readiness-assessment-for-charities/ |
| 13 | 1 | AI readiness assessment for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/ai-readiness-assessment-for-healthcare-education/ |
| 14 | 1 | AI readiness assessment for professional services firms | WebAwesome | https://www.webawesome.co.uk/ai-readiness-assessment-for-professional-services/ |
| 15 | 1 | AI readiness assessment for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/ai-readiness-assessment-for-trades-field-service/ |
| 16 | 1 | AI governance and risk for small businesses | WebAwesome | https://www.webawesome.co.uk/ai-governance-risk-for-small-business/ |
| 17 | 1 | AI governance and risk for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/ai-governance-risk-for-charities/ |
| 18 | 1 | AI governance and risk for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/ai-governance-risk-for-healthcare-education/ |
| 19 | 1 | AI governance and risk for professional services firms | WebAwesome | https://www.webawesome.co.uk/ai-governance-risk-for-professional-services/ |
| 20 | 1 | AI governance and risk for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/ai-governance-risk-for-trades-field-service/ |
| 21 | 2 | WordPress websites for small businesses | WebAwesome | https://www.webawesome.co.uk/wordpress-websites-for-small-business/ |
| 22 | 2 | WordPress websites for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/wordpress-websites-for-charities/ |
| 23 | 2 | WordPress websites for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/wordpress-websites-for-healthcare-education/ |
| 24 | 2 | WordPress websites for professional services firms | WebAwesome | https://www.webawesome.co.uk/wordpress-websites-for-professional-services/ |
| 25 | 2 | WordPress websites for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/wordpress-websites-for-trades-field-service/ |
| 26 | 2 | Website redesign for small businesses | WebAwesome | https://www.webawesome.co.uk/website-redesign-for-small-business/ |
| 27 | 2 | Website redesign for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/website-redesign-for-charities/ |
| 28 | 2 | Website redesign for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/website-redesign-for-healthcare-education/ |
| 29 | 2 | Website redesign for professional services firms | WebAwesome | https://www.webawesome.co.uk/website-redesign-for-professional-services/ |
| 30 | 2 | Website redesign for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/website-redesign-for-trades-field-service/ |
| 31 | 2 | Accessible websites for small businesses | WebAwesome | https://www.webawesome.co.uk/accessible-websites-for-small-business/ |
| 32 | 2 | Accessible websites for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/accessible-websites-for-charities/ |
| 33 | 2 | Accessible websites for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/accessible-websites-for-healthcare-education/ |
| 34 | 2 | Accessible websites for professional services firms | WebAwesome | https://www.webawesome.co.uk/accessible-websites-for-professional-services/ |
| 35 | 2 | Accessible websites for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/accessible-websites-for-trades-field-service/ |
| 36 | 2 | Booking websites for small businesses | WebAwesome | https://www.webawesome.co.uk/booking-websites-for-small-business/ |
| 37 | 2 | Booking websites for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/booking-websites-for-charities/ |
| 38 | 2 | Booking websites for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/booking-websites-for-healthcare-education/ |
| 39 | 2 | Booking websites for professional services firms | WebAwesome | https://www.webawesome.co.uk/booking-websites-for-professional-services/ |
| 40 | 2 | Booking websites for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/booking-websites-for-trades-field-service/ |
| 41 | 3 | Custom web apps for small businesses | WebAwesome | https://www.webawesome.co.uk/custom-web-apps-for-small-business/ |
| 42 | 3 | Custom web apps for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/custom-web-apps-for-charities/ |
| 43 | 3 | Custom web apps for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/custom-web-apps-for-healthcare-education/ |
| 44 | 3 | Custom web apps for professional services firms | WebAwesome | https://www.webawesome.co.uk/custom-web-apps-for-professional-services/ |
| 45 | 3 | Custom web apps for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/custom-web-apps-for-trades-field-service/ |
| 46 | 3 | Internal tools for small businesses | WebAwesome | https://www.webawesome.co.uk/internal-tools-for-small-business/ |
| 47 | 3 | Internal tools for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/internal-tools-for-charities/ |
| 48 | 3 | Internal tools for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/internal-tools-for-healthcare-education/ |
| 49 | 3 | Internal tools for professional services firms | WebAwesome | https://www.webawesome.co.uk/internal-tools-for-professional-services/ |
| 50 | 3 | Internal tools for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/internal-tools-for-trades-field-service/ |
| 51 | 3 | CRM automation for small businesses | WebAwesome | https://www.webawesome.co.uk/crm-automation-for-small-business/ |
| 52 | 3 | CRM automation for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/crm-automation-for-charities/ |
| 53 | 3 | CRM automation for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/crm-automation-for-healthcare-education/ |
| 54 | 3 | CRM automation for professional services firms | WebAwesome | https://www.webawesome.co.uk/crm-automation-for-professional-services/ |
| 55 | 3 | CRM automation for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/crm-automation-for-trades-field-service/ |
| 56 | 3 | Workflow automation for small businesses | WebAwesome | https://www.webawesome.co.uk/workflow-automation-for-small-business/ |
| 57 | 3 | Workflow automation for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/workflow-automation-for-charities/ |
| 58 | 3 | Workflow automation for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/workflow-automation-for-healthcare-education/ |
| 59 | 3 | Workflow automation for professional services firms | WebAwesome | https://www.webawesome.co.uk/workflow-automation-for-professional-services/ |
| 60 | 3 | Workflow automation for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/workflow-automation-for-trades-field-service/ |
| 61 | 4 | Digital consulting for small businesses | WebAwesome | https://www.webawesome.co.uk/digital-consulting-for-small-business/ |
| 62 | 4 | Digital consulting for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/digital-consulting-for-charities/ |
| 63 | 4 | Digital consulting for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/digital-consulting-for-healthcare-education/ |
| 64 | 4 | Digital consulting for professional services firms | WebAwesome | https://www.webawesome.co.uk/digital-consulting-for-professional-services/ |
| 65 | 4 | Digital consulting for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/digital-consulting-for-trades-field-service/ |
| 66 | 4 | Digital strategy for small businesses | WebAwesome | https://www.webawesome.co.uk/digital-strategy-for-small-business/ |
| 67 | 4 | Digital strategy for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/digital-strategy-for-charities/ |
| 68 | 4 | Digital strategy for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/digital-strategy-for-healthcare-education/ |
| 69 | 4 | Digital strategy for professional services firms | WebAwesome | https://www.webawesome.co.uk/digital-strategy-for-professional-services/ |
| 70 | 4 | Digital strategy for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/digital-strategy-for-trades-field-service/ |
| 71 | 4 | Discovery call with small businesses | WebAwesome | https://www.webawesome.co.uk/discovery-call-for-small-business/ |
| 72 | 4 | Discovery call with charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/discovery-call-for-charities/ |
| 73 | 4 | Discovery call with healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/discovery-call-for-healthcare-education/ |
| 74 | 4 | Discovery call with professional services firms | WebAwesome | https://www.webawesome.co.uk/discovery-call-for-professional-services/ |
| 75 | 4 | Discovery call with trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/discovery-call-for-trades-field-service/ |
| 76 | 4 | Systems integration for small businesses | WebAwesome | https://www.webawesome.co.uk/systems-integration-for-small-business/ |
| 77 | 4 | Systems integration for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/systems-integration-for-charities/ |
| 78 | 4 | Systems integration for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/systems-integration-for-healthcare-education/ |
| 79 | 4 | Systems integration for professional services firms | WebAwesome | https://www.webawesome.co.uk/systems-integration-for-professional-services/ |
| 80 | 4 | Systems integration for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/systems-integration-for-trades-field-service/ |
| 81 | 5 | AIOS for small businesses | WebAwesome | https://www.webawesome.co.uk/aios-for-small-business/ |
| 82 | 5 | AIOS for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/aios-for-charities/ |
| 83 | 5 | AIOS for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/aios-for-healthcare-education/ |
| 84 | 5 | AIOS for professional services firms | WebAwesome | https://www.webawesome.co.uk/aios-for-professional-services/ |
| 85 | 5 | AIOS for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/aios-for-trades-field-service/ |
| 86 | 5 | Solutions consulting for small businesses | WebAwesome | https://www.webawesome.co.uk/solutions-consulting-for-small-business/ |
| 87 | 5 | Solutions consulting for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/solutions-consulting-for-charities/ |
| 88 | 5 | Solutions consulting for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/solutions-consulting-for-healthcare-education/ |
| 89 | 5 | Solutions consulting for professional services firms | WebAwesome | https://www.webawesome.co.uk/solutions-consulting-for-professional-services/ |
| 90 | 5 | Solutions consulting for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/solutions-consulting-for-trades-field-service/ |
| 91 | 5 | Business process review for small businesses | WebAwesome | https://www.webawesome.co.uk/business-process-review-for-small-business/ |
| 92 | 5 | Business process review for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/business-process-review-for-charities/ |
| 93 | 5 | Business process review for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/business-process-review-for-healthcare-education/ |
| 94 | 5 | Business process review for professional services firms | WebAwesome | https://www.webawesome.co.uk/business-process-review-for-professional-services/ |
| 95 | 5 | Business process review for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/business-process-review-for-trades-field-service/ |
| 96 | 5 | AI ROI measurement for small businesses | WebAwesome | https://www.webawesome.co.uk/ai-roi-measurement-for-small-business/ |
| 97 | 5 | AI ROI measurement for charities and nonprofits | WebAwesome | https://www.webawesome.co.uk/ai-roi-measurement-for-charities/ |
| 98 | 5 | AI ROI measurement for healthcare and education providers | WebAwesome | https://www.webawesome.co.uk/ai-roi-measurement-for-healthcare-education/ |
| 99 | 5 | AI ROI measurement for professional services firms | WebAwesome | https://www.webawesome.co.uk/ai-roi-measurement-for-professional-services/ |
| 100 | 5 | AI ROI measurement for trades and field-service businesses | WebAwesome | https://www.webawesome.co.uk/ai-roi-measurement-for-trades-field-service/ |

### Go-live gate and kill rule (agreed 2026-11-20)

- Do not publish all 100 at once. Ship 20 per week at the earliest, and only after the 50 geo pages pass the first indexation check.
- Before each tranche: confirm Google Search Console access, record the baseline, and check the Search Status Dashboard for an active core/spam update.
- Indexation gate: at least 90% of a published batch indexed within 30 days. Below that, pause publishing and fix or consolidate before the next batch.
- Kill rule: a page with zero impressions after 60 days gets merged into a stronger page with a 301 redirect, noindexed, or removed. Review monthly, not after a penalty.
- Add the canonical URLs to the domain root sitemap as each batch goes live.
- These pages are synthetically differentiated, not backed by first-party project evidence. Add a real example, client quote or original data point to each page before publishing where possible.

## Before building a new one

1. Search this file for the region, topic, service and slug you have in mind.
2. If a matching page exists, update it rather than creating another — near-duplicate geo pages risk thin-content/doorway-page penalties.
3. For new WebAwesome geo pages, add the entry to `ENTRIES` in `scripts/generate-geo-microsites.py` and run the generator.
4. For new keyword-campaign pages, add the topic to `TOPICS` in `scripts/generate-keyword-microsites.py` and run the generator.
5. Add the new canonical URLs to the domain root sitemap, then append them here.
