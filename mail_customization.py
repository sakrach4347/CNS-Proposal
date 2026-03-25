import csv
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests

# Load environment variables from .env file
load_dotenv()


def google_search(query, api_key, cse_id):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"q": query, "key": api_key, "cx": cse_id}
    response = requests.get(url, params=params)
    results = response.json()
    snippets = []
    for item in results.get("items", []):
        snippets.append(item.get("snippet", ""))
    return "\n".join(snippets[:3])  # Use top 3 snippets


def generate_mail_csv(input_csv, output_csv):
    consultant_name = input("Enter consultant name: ")
    consultant_email = input("Enter consultant email: ")

    # Configure the Gemini API key from environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
        return
    genai.configure(api_key=gemini_api_key)

    context="""🔹 1. ManCrafters (BR Business Solutions)

    Domain: Men’s Grooming & Personal Care Marketplace
    Type: Strategic Sales Consulting + Market Research + Brand Strategy

    About:
    BR Business Solutions (d/b/a ManCrafters) is a strategic sales consulting firm focused on brand growth and market development. Under its umbrella, ManCrafters was conceptualized as a dedicated B2C marketplace for men’s grooming and personal care products, curating brands based on consumer preferences and emerging trends.

    180DC’s Role:

    Conducted consumer behaviour and market trend analysis to map the gaps in India’s grooming market.

    Delivered competitive branding and positioning strategy to differentiate ManCrafters from mass retail players.

    Designed strategic recommendations for marketplace development, including onboarding and vendor acquisition plans.

    Key Verticals:

    Market Research & Insights

    Competitive & Branding Strategies

    Marketplace Development Plans

    🔹 2. Chef Scripts

    Domain: Luxury Catering & Cloud Kitchen Expansion
    Type: Food Service Strategy + Expansion Planning

    About:
    Chef Scripts is a premium catering brand based in Delhi NCR, offering corporate, wedding and live-station catering services. The company prides itself on its culinary standards and personalized event experiences.

    180DC’s Role:

    Developed a market expansion roadmap for new cities and regional markets.

    Identified high-growth food industry models, especially for cloud kitchen integration.

    Recommended pricing structures, operational models, and growth avenues for scalability.

    Key Verticals:

    Corporate Catering & Event Services

    Outdoor & Wedding Catering

    Cloud Kitchen Expansion Strategy

    🔹 3. Trumio Inc.

    Domain: Ed-Tech & Industry-Academia Collaboration
    Type: Startup Consulting + Community Building + Funding Strategy

    About:
    Trumio is a startup that bridges corporate projects and college students via an online portal. It helps businesses outsource project work to college students (primarily sophomores and third-years), offering externship opportunities that build career readiness.

    180DC’s Role:

    Structured Trumio Chapters as college societies to drive career awareness and skill projects.

    Created funding pitch decks and outreach material for investor presentations.

    Recommended digital engagement and optimization strategies for portal growth and user retention.

    Key Verticals:

    Industry-Academia Collaboration

    Student Career Development

    Digital Engagement & Optimization

    🔹 4. Indeanta E-Mobility

    Domain: Electric Mobility & Transport Strategy
    Type: Market Entry + Go-To-Market (GTM) Execution

    About:
    Founded in 2021 and based in Mangaluru, Karnataka, Indeanta is India’s first multi-modal all-electric transport service provider, operating e-bikes and shuttles on college campuses to enable low-cost, efficient mobility with seamless app integration.

    180DC’s Role:

    Devised a Go-To-Market and implementation strategy for IIT Kharagpur’s launch.

    Built a comprehensive operational roadmap, covering logistics, partnerships, and user experience.

    Delivered smart mobility solution recommendations based on cost, sustainability, and campus demographics.

    Key Verticals:

    Market Strategy & GTM Execution

    Operational Roadmap & Implementation

    Smart Mobility Solutions

    🔹 5. Guntur Impact Fund

    Domain: Social Impact & Rural Development
    Type: Government-Linked NGO Strategy + Employment Model Design

    About:
    Guntur Impact Fund is a not-for-profit organization based in Andhra Pradesh, operating under the guidance of the Union Minister of State for Rural Development. It focuses on sustainable livelihoods and local economic growth through Central Government schemes.

    180DC’s Role:

    Designed self-sustainable employment models for rural youth and women.

    Developed scalable implementation frameworks for Central Government programs.

    Assisted in local impact measurement and economic feasibility studies.

    Key Verticals:

    Employment Creation & Skill Development

    Sustainable Economic Models

    Government Scheme Implementation

    🔹 6. Past Flagship Projects (from 180DC Brochure)

    These projects built the foundation of 180DC IIT Kharagpur’s credibility and reputation:

    Client / Partner	Domain	Key Contributions
    The Washing Machine Project (UK)	Social Innovation	Supply chain & manufacturing efficiency strategy for affordable manual washing machines.
    Dept. of Commercial Tax, MP Govt.	Policy & Revenue	Proposed revenue recovery models post-COVID; policy liberalization & e-licensing reforms.
    Falhari Foods	FMCG	Market research on fasting foods; product placement and marketing strategy.
    Empass (AmazeTests)	Ed-Tech	Market entry & client acquisition approach for psychometric testing in schools.
    Mahila Saksham Foundation	Women Empowerment	Employment strategy for rural women affected by COVID-19.
    World Vision India	Employment Research	Survey analysis on youth unemployment and skill gap bridging.
    Genesis Foundation	Healthcare NGO	NGO sustainability model and financial collaboration analysis.
    The Yarn Bazaar	Startup & Logistics	Designed reverse logistics and distribution system for yarn packaging.
    Cuddles Foundation	Healthcare NGO	Devised volunteer conversion strategy and market entry plan.
    Robin Hood Army	Hunger Alleviation	Legal framework for FSSAI partnership and alternative licensing routes.
    🔹 7. Overall Themes & Capabilities

    Across these projects, 180DC IIT Kharagpur demonstrated capabilities in:

    Market Research & Growth Strategy (FMCG, Mobility, Food Services)

    Operational Optimization & Roadmaps (Startups, NGOs)

    Policy & Social Impact Consulting (Government and Rural Development)

    Digital Transformation & Engagement (Ed-Tech and Career Portals)

    Sustainability & Employment Model Design (Impact Funds, Foundations)"""

    # Use a supported model name
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    with open(input_csv, "r", encoding="utf-8") as f_in, open(
        output_csv, "w", newline="", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["From", "To", "Subject", "Body", "POC_Name", "Organization"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Extract data from Apollo CSV columns
            first_name = row.get("First Name", "")
            last_name = row.get("Last Name", "")
            title = row.get("Title", "")
            company_name = row.get("Company Name for Emails", "") or row.get("Company", "")
            email = row.get("Email", "")
            industry = row.get("Industry", "")
            keywords = row.get("Keywords", "")
            city = row.get("City", "")
            state = row.get("State", "")
            country = row.get("Country", "")
            company_city = row.get("Company City", "")
            company_state = row.get("Company State", "")
            company_country = row.get("Company Country", "")
            technologies = row.get("Technologies", "")
            website = row.get("Website", "")
            linkedin_url = row.get("Person Linkedin Url", "")
            company_linkedin = row.get("Company Linkedin Url", "")
            num_employees = row.get("# Employees", "")
            annual_revenue = row.get("Annual Revenue", "")
            
            # Create POC name and location info
            poc_name = f"{first_name} {last_name}".strip()
            if not poc_name:
                poc_name = "Team"
            
            location = f"{city}, {state}, {country}".strip(", ")
            company_location = f"{company_city}, {company_state}, {company_country}".strip(", ")
            
            # Skip if no email
            if not email:
                continue

            # Fetch extra info from Google Search
            google_api_key = os.getenv("GOOGLE_API_KEY")
            google_cse_id = os.getenv("GOOGLE_CSE_ID")
            search_snippets = google_search(
                f"{company_name} about", google_api_key, google_cse_id
            )

            # Detailed system prompt with Apollo data
            prompt_text = (
                "You are an expert business consultant tasked with writing highly professional, "
                "personalized outreach emails to companies. Each email should include:\n"
                "- A compelling, relevant subject line.\n"
                "- A detailed, friendly, and professional body that references the company's background and mission.\n"
                "- The email should be from the consultant (details below) to the company (details below).\n"
                "- Do not include any labels like 'Subject:' or 'Body:'.\n"
                "- The output must be the subject line, then a newline, then the full email body.\n"
                "- The email should be suitable for a first contact and encourage a reply.\n"
                "- The length limit is two paragraphs, be detailed on what 180DC IITKGP can offer to them and be direct.\n"
                "Here is a sample mail, you must refer to a similar format only for sending the mails - Change it according to the Company you are reaching out to and according to the necessary context i'll provide.\n"
                "4 paras, add word limit (not more than 250-300 words)\n"
                "1st para: intro\n"
                "2nd para: what do we do (whom all we have worked with)\n"
                "3rd: butter them up, keen to work with you, how we can add value.\n"
                "4th: conclusion. We would love to discuss this further. \n"
                "CRITICAL FORMATTING REQUIREMENT: You MUST use double newlines (\\n\\n) between EVERY paragraph. Do not use single newlines.\n\n"
                "TEMPLATE:\n"
                "Respected Sir,\n\n"
                f"I am {consultant_name}, a Consultant at 180 Degrees Consulting, IIT Kharagpur. Thank you for your response on LinkedIn. We're a student-run body that is passionate about providing operational and strategic services to NGOs and social enterprises, and be a part of their growth and impact journey.\n\n"
                "We have been greatly influenced by the powerful contributions of Terre des hommes foundation in protecting children's rights and well-being and provide vital protection through core programs. Your efforts have profoundly impacted the lives of countless individuals through the events you organize and the awareness you generate.\n\n"
                "We at 180DC IIT Kharagpur have worked with organizations such as the CRY Foundation and Robin Hood Army, aiding them in improving operations, strategic growth, and program outcomes. We feel our services may assist Terre des hommes cause by multiplying its impact through strategy and operational consulting.\n\n"
                "We would be delighted to reach out to you and learn about how we can work together. To provide more insights about our organisation I have attached our brochure. We look forward to speaking with you and your team!\n\n"
                "Best regards,\n"
                f"{consultant_name}\n"
                "Consultant\n"
                "180 Degrees Consulting, IIT Kharagpur\n"
                "https://www.180dc.org/branches/IITKGP\n\n"
                "This must be modified according to the purpose and nature of the company, you may perform google search and online research to find more information about the company.\n"
                f"Consultant Name: {consultant_name}\n"
                f"Consultant Email: {consultant_email}\n"
                f"POC Name: {poc_name}\n"
                f"POC Title: {title}\n"
                f"Company Name: {company_name}\n"
                f"Industry: {industry}\n"
                f"Company Keywords: {keywords}\n"
                f"Company Location: {company_location}\n"
                f"Technologies: {technologies}\n"
                f"Company Website: {website}\n"
                f"Number of Employees: {num_employees}\n"
                f"Annual Revenue: {annual_revenue}\n"
                f"Recent Google Search Results: {search_snippets}\n"
                f"Necessary 180DC IIT KGP Context:{context}"
            )

            try:
                response = model.generate_content(prompt_text)
                generated_text = (
                    response.text
                    if hasattr(response, "text")
                    else (
                        response.generations[0].content if response.generations else ""
                    )
                )
                text_output = generated_text.strip().split("\n", 1)
                
                # Robust extraction and cleanup
                subject_line = text_output[0].strip() if text_output else "Following Up"
                if subject_line.lower().startswith("subject:"):
                    subject_line = subject_line[8:].strip()
                    
                body_text = (
                    text_output[1].strip()
                    if len(text_output) > 1
                    else "Could not generate email body."
                )
                if body_text.lower().startswith("body:"):
                    body_text = body_text[5:].strip()
                    
            except Exception as e:
                print(f"Error generating content for {company_name}: {e}")
                subject_line = f"Introduction from {consultant_name}"
                body_text = f"Dear {company_name} team,\n\nI am writing to introduce our consulting services..."

            writer.writerow(
                {
                    "From": consultant_email,
                    "To": email,
                    "Subject": subject_line,
                    "Body": body_text,
                    "POC_Name": poc_name,
                    "Organization": company_name,
                }
            )
        print(f"Successfully generated mails in {output_csv}")


if __name__ == "__main__":
    input_csv_path = r".\apollo-contacts-export.csv"
    output_csv_path = r".\generated_mails-5.csv"
    generate_mail_csv(input_csv_path, output_csv_path)

