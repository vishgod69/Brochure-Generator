# AI Brochure Generator

A Python application that analyzes a company website and generates a business brochure in English and Spanish using the OpenAI API.

## Functionality

The program:

* Collects links from a company website
* Uses an LLM to select relevant pages
* Scrapes content from the homepage and selected pages
* Generates an English brochure in Markdown
* Translates the brochure into Spanish
* Saves both brochures as `.md` files

## Technologies and Capabilities

* Python application development
* OpenAI API integration
* Prompt engineering
* Multistep LLM workflows
* JSON response parsing
* Environment variable management
* Command-line input handling

## Requirements

* Python 3.12
* An OpenAI API key or alternative
* Internet access

## Installation

Clone the repository

Install the required packages

Open the `.env` file and replace the placeholder with your API key

If necessary add url and api to the openai initialization

Run the program:

```bash
py -3.12 generate_brochure.py
```

Enter the company name and website URL when prompted.

The English and Spanish brochures will be saved in the `generated_brochures` folder.

## License

This project was created for educational and portfolio purposes.

