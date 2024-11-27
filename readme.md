# PersonalChat

## Information
This Project is a Chatbot that answer to queries based on its documentation stored.
It reads PDFs and integrate them in a Chroma database.
For now, the documentation used is only a CV but other files can be added.

### User Guide
#### Prerequisites
Get the embeddings and LLM models :
- Install [Ollama](https://ollama.com/)
- In Ollama terminal, load the embedding model with "ollama pull nomic-embed-text"
- In Ollama terminal, load the LLM model with "ollama pull mistral"

Install the relevant python libraries :
> pip install -r requirements

#### Start the application
 > python manage.py runserver

Go to *http://127.0.0.1:8000/*

#### Send a query
- Write the query in the input box
- Click on "Send"
- Wait for the chatbot to answer you

#### Populate the database
- Add a PDF in the "data" folder
- Send the query "Populate" to the chatbot

#### Clear the database
- Send the query "Clear" to the chatbot

## Functionalities
- [x] Send a query  
- [x] Receive an answer based on the information stored in the database  
- [x] Populate the database  
- [x] Clear the database  

## Sources
- Video : ["Python RAG Tutorial (with Local LLMs): AI For Your PDFs"](https://www.youtube.com/watch?v=2TJxpyO3ei4)
of pixegami
- Video : ["Django ChatGPT Clone Tutorial"](https://www.youtube.com/watch?v=qrZGfBBlXpk) of freeCodeCamp.org
