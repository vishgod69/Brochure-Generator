import os
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
from pathlib import Path

#saving brochures into markdown files
def save_markdown(markdown_text, filename):
    output_folder = Path("generated_brochures")
    output_folder.mkdir(parents=True, exist_ok=True)

    markdown_path = output_folder / f"{filename}.md"
    markdown_path.write_text(markdown_text, encoding="utf-8")

    print(f"Markdown saved to: {markdown_path}")

    return markdown_path

# Webscraping tools were taken from Ed Donner's LLM Engineer Udemy Course
# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]

#setting up openai api with api key
#replace gpt-5-nano here if you want, its only used in the first call
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-5-nano'

#if you want to use a different model:
#base_url = url for model you want to use
#api_key = provider api key
openai = OpenAI()

#first system prompt to get relevant links
link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

#first user prompt to get relevant links
def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt

#calls gpt5 with all links to filter out only good and relevant ones for the brochure
def select_relevant_links(url):
    response = openai.chat.completions.create(
        model=MODEL,
        messages = [
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"found {len(links['links'])} relevant links")
    return links

#grabs all the content from relevant links returned in select_relevant_links
def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

#system prompt to generate brochure
brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

#user prompt to generate brochure
def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
    return user_prompt

#brochure being generated
def create_brochure(company_name, url):
    content = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    result = content.choices[0].message.content
    return result

#spanish system prompt
spanish_brochure_prompt = """
You are a spanish translator that can translate lots of text from English to Spanish.
You will be given a brochure and you will translate the brochure from english to spanish.
Make sure the format of the brochure is the same as given, just translate.
"""

#spanish user prompt
def spanish_user_prompt(company_name, brochure):
    user_prompt = f"""
You are given a brochure from the company: {company_name}
Generate a translated brochure with the same format, except in spanish

"""
    user_prompt += brochure
    return user_prompt
    
#uses brochure generated from english version to create spanish version
def create_brochure_spanish(company_name, brochure):
    content = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": spanish_brochure_prompt},
            {"role": "user", "content": spanish_user_prompt(company_name, brochure)}
          ],
    )    
    response = content.choices[0].message.content
    return response

def main():
    company_name = input("Enter the company name: ")
    company_url = input("Enter the company website URL: ")

    brochure = create_brochure(company_name, company_url)
    spanish_brochure = create_brochure_spanish(company_name, brochure)

    save_markdown(
        markdown_text=brochure,
        filename=f"{company_name}_brochure"
    )

    save_markdown(
        markdown_text=spanish_brochure,
        filename=f"{company_name}_brochure_spanish"
    )

    print("Brochures have been created!")


if __name__ == "__main__":
    main()