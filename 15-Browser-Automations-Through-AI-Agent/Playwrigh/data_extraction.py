import json
from bs4 import BeautifulSoup

def clean_text(text):
    """A helper function to clean up extracted text and handle NoneTypes."""
    if text:
        return ' '.join(text.strip().split())
    return None

def extract_linkedin_profile(html_file_path):
    """
    Parses a saved LinkedIn profile HTML file and extracts key information robustly.
    """
    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'lxml')

    profile_data = {
        "personal_info": {},
        "connection_details": {},
        "about": None,
        "experience": [],
        "education": [],
        "licenses_certifications": [],
        "featured_section": [],
        "key_skills": []
    }

    # --- 1. Personal & Connection Info ---
    top_card = soup.find('section', class_='artdeco-card')
    if top_card:
        name_h1 = top_card.find('h1')
        if name_h1:
            profile_data["personal_info"]["name"] = clean_text(name_h1.get_text())

        headline_div = top_card.find('div', class_='text-body-medium')
        if headline_div:
            profile_data["personal_info"]["headline"] = clean_text(headline_div.get_text())

        location_span = top_card.find('span', class_='text-body-small inline t-black--light break-words')
        if location_span:
            profile_data["personal_info"]["location"] = clean_text(location_span.get_text())

        contact_info_link = top_card.find('a', id='top-card-text-details-contact-info')
        if contact_info_link:
            profile_data["personal_info"]["contact_info_url"] = "https://www.linkedin.com" + contact_info_link['href']
        
        public_profile_a = top_card.find('a', href=lambda href: href and '/in/' in href)
        if public_profile_a:
             profile_data["personal_info"]["public_profile_url"] = public_profile_a.get('href', '').split('?')[0]


        connection_degree_span = top_card.find('span', class_='dist-value')
        if connection_degree_span:
            profile_data["connection_details"]["connection_degree"] = clean_text(connection_degree_span.get_text())

        connections_link = top_card.find('a', href=lambda href: href and 'results/people' in href)
        if connections_link:
            connections_span = connections_link.find('span', class_='t-bold')
            if connections_span:
                try:
                    profile_data["connection_details"]["connections_count"] = int(clean_text(connections_span.get_text()))
                except (ValueError, TypeError):
                    profile_data["connection_details"]["connections_count"] = 0

    # --- 2. About Section ---
    about_section_anchor = soup.find('div', id='about')
    if about_section_anchor:
        about_card = about_section_anchor.find_parent('section')
        if about_card:
            about_text_span = about_card.find('span', {'aria-hidden': 'true'})
            if about_text_span:
                profile_data["about"] = clean_text(about_text_span.get_text())

    # --- 3. Featured Section ---
    featured_section_anchor = soup.find('div', id='featured')
    if featured_section_anchor:
        featured_card = featured_section_anchor.find_parent('section')
        if featured_card:
            featured_items = featured_card.select('ul.artdeco-carousel__slider > li')
            for item in featured_items:
                featured_entry = {}
                # Extract type, title, description, and link
                type_span = item.find('div', class_='pvs-content__top-bar')
                if type_span and type_span.find('span', {'aria-hidden': 'true'}):
                     featured_entry['type'] = clean_text(type_span.find('span', {'aria-hidden': 'true'}).get_text())
                
                title_div = item.find('div', class_='text-heading-small')
                if title_div and title_div.find('span', {'aria-hidden': 'true'}):
                     featured_entry['title'] = clean_text(title_div.find('span', {'aria-hidden': 'true'}).get_text())

                desc_div = item.find('div', class_='text-body-small')
                if desc_div and desc_div.find('span', {'aria-hidden': 'true'}):
                     featured_entry['description'] = clean_text(desc_div.find('span', {'aria-hidden': 'true'}).get_text())
                
                link_tag = item.find('a', class_='optional-action-target-wrapper')
                if link_tag:
                    featured_entry['link'] = link_tag.get('href')

                if featured_entry: # Only add if we found something
                    profile_data["featured_section"].append(featured_entry)

    # --- 4. Experience Section ---
    experience_section_anchor = soup.find('div', id='experience')
    if experience_section_anchor:
        experience_card = experience_section_anchor.find_parent('section')
        if experience_card:
            experience_items = experience_card.find_all('li', class_='artdeco-list__item')
            for item in experience_items:
                title_span = item.find('div', class_='display-flex').find('span', {'aria-hidden': 'true'})
                if not title_span: continue
                
                experience_entry = {'title': clean_text(title_span.get_text())}
                
                spans = item.find_all('span', {'aria-hidden': 'true'})
                # This logic assumes a consistent structure, might need adjustment
                if len(spans) > 2:
                    experience_entry['company'] = clean_text(spans[2].get_text().split('·')[0])
                    experience_entry['duration'] = clean_text(spans[3].get_text()) if len(spans) > 3 else None
                    experience_entry['location'] = clean_text(spans[4].get_text()) if len(spans) > 4 else None

                desc_div = item.find('div', class_='inline-show-more-text')
                if desc_div and desc_div.find('span', {'aria-hidden': 'true'}):
                   experience_entry['description'] = clean_text(desc_div.find('span', {'aria-hidden': 'true'}).get_text())

                profile_data["experience"].append(experience_entry)

    # --- 5. Education Section ---
    education_section_anchor = soup.find('div', id='education')
    if education_section_anchor:
        education_card = education_section_anchor.find_parent('section')
        if education_card:
            education_items = education_card.find_all('li', class_='artdeco-list__item')
            for item in education_items:
                education_entry = {}
                school_name_span = item.find('span', class_='mr1 hoverable-link-text t-bold')
                if school_name_span and school_name_span.find('span', {'aria-hidden': 'true'}):
                    education_entry['institution'] = clean_text(school_name_span.find('span', {'aria-hidden': 'true'}).get_text())

                degree_span = item.find('span', class_='t-14 t-normal')
                if degree_span and degree_span.find('span', {'aria-hidden': 'true'}):
                    education_entry['degree'] = clean_text(degree_span.find('span', {'aria-hidden': 'true'}).get_text())
                
                duration_span = item.find('span', class_='t-14 t-normal t-black--light')
                if duration_span and duration_span.find('span', {'aria-hidden': 'true'}):
                    education_entry['duration'] = clean_text(duration_span.find('span', {'aria-hidden': 'true'}).get_text())
                
                if education_entry:
                    profile_data["education"].append(education_entry)

    # --- 6. Licenses & Certifications ---
    cert_section_anchor = soup.find('div', id='licenses_and_certifications')
    if cert_section_anchor:
        cert_card = cert_section_anchor.find_parent('section')
        if cert_card:
            cert_items = cert_card.find_all('li', class_='artdeco-list__item')
            for item in cert_items:
                cert_entry = {}
                name_span = item.find('div', class_='display-flex').find('span', {'aria-hidden': 'true'})
                if name_span:
                    cert_entry['name'] = clean_text(name_span.get_text())

                org_span = item.select_one('span.t-14.t-normal span[aria-hidden="true"]')
                if org_span:
                    cert_entry['issuing_organization'] = clean_text(org_span.get_text())
                
                date_span = item.select_one('span.t-14.t-normal.t-black--light span[aria-hidden="true"]')
                if date_span:
                    cert_entry['issue_date'] = clean_text(date_span.get_text())

                credential_link = item.find('a', href=lambda href: href and 'http' in href)
                if credential_link:
                    cert_entry['credential_url'] = credential_link['href']
                
                if cert_entry:
                    profile_data["licenses_certifications"].append(cert_entry)

    # --- 7. Skills ---
    skills_section_anchor = soup.find('div', id='skills')
    if skills_section_anchor:
        skills_card = skills_section_anchor.find_parent('section')
        if skills_card:
            # This gets the top skills from the 'About' section highlight
            top_skills_div = soup.select_one('div[data-view-name="profile-component-entity"]:-soup-contains("Top skills")')
            if top_skills_div:
                skills_text_span = top_skills_div.find('span', {'aria-hidden': 'true'}, text=lambda t: '•' in t)
                if skills_text_span:
                    skills = [skill.strip() for skill in skills_text_span.get_text().split('•')]
                    profile_data['key_skills'] = skills
    
    return profile_data


# --- Main execution ---
if __name__ == "__main__":
    # html_file = "Md_Al_Amin___LinkedIn.html"
    # html_file = "Abdullah_Matin___LinkedIn.html"
    # html_file = "Rubayet_Faisal___LinkedIn.html"
    html_file = "Faiaz_Hossain_Nirob___LinkedIn.html"
    
    try:
        extracted_data = extract_linkedin_profile(html_file)
        
        # Convert the dictionary to a JSON string with indentation
        json_output = json.dumps(extracted_data, indent=4)
        
        # Print the beautiful JSON output
        print(json_output)

        # Optionally, save to a file
        with open("linkedin_profile_data.json", "w", encoding='utf-8') as f:
            f.write(json_output)
        print(f"\n[SUCCESS] Data successfully extracted and saved to 'linkedin_profile_data.json'")

    except FileNotFoundError:
        print(f"[ERROR] The file '{html_file}' was not found. Make sure it's in the same directory as the script.")
    except Exception as e:
        import traceback
        print(f"[ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()