import os
import shutil
from langchain.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from django.shortcuts import render
from django.http import JsonResponse
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms.ollama import Ollama

CHROMA_PATH = "chroma"
DATA_PATH = "data"
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

def get_embedding_function():
    """
    Get the embedding function.

    :return: The embedding function
    """
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

def load_documents():
    """
    Load PDF documents from the "data" repository.
    :return: (list[langchain Document]) The list of the documents
    """
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def split_documents(documents: list[Document]):
    """
    Split the documents into chunks.

    :param documents: (list[langchain Document]) The list of the documents
    :return: (list[langchain Document]) The list of chunks of documents
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks: list[Document]):
    """
    Add the documents (split into chunks) to Chroma database.

    :param chunks: (list[langchain Document]) The list of chunks of documents
    """
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    # Calculate chunks identifiers.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the database.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        #db.persist()
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks):
    """
    Compute the chunks identifiers in order to have unique chunks.

    :param chunks: (list[Document]) list of documents.
    :return: (list[Document]) Chunks with computed identifier in the metadata.
    """

    # This will create identifiers like "[file name]:[page number]:[chunk index]"

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    """
    Clear the database (remove all the files)
    """
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

def ask_chroma(message, n_results=4):
    """
    Answer to a query using the context in Chroma database.

    :param message: (string) Message given as the query to the model.
    :param n_results: (integer) Number of results/contexts the model will look at to answer to the query. Default : n_results=4.
    :return: The answer to the query with the sources used as the context.
    """
    # Prepare the database.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search in the database.
    results = db.similarity_search_with_score(message, n_results)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=message)
    # print(prompt)

    model = Ollama(model="mistral")
    answer = model.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {answer}<br>Sources: {sources}"
    print(formatted_response)
    return formatted_response

def populate_database():
    """
    Create or Update the database with the new documents given.
    """
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)

def chatbot(request):
    """
    Chatbot render. Compute and return an answer when a query is submitted.

    :param request: request received. If it is a POST request, the "message" argument is taken as the query.
        - if the query is "Populate" : the chroma database is populated with the new documents in the "data" repository
        - if the query is "Clear" : the Chroma database is cleared.
        - otherwise the query is the input to Olloma Chat model
    :return: (JsonResponse({'message':string,'response':string}) Answer of the chatbot
    """
    if request.method == 'POST':
        message = request.POST.get('message')
        if message == "Populate":
            print("Populate Database")
            populate_database()
            return JsonResponse({
                'message': message,
                'response': "Database populated"
            })
        elif message == "Clear":
            print("Clear Database")
            clear_database()
            return JsonResponse({
                'message': message,
                'response': "Database cleared"
            })
        else :
            response = ask_chroma(message)
            return JsonResponse({
                'message':message,
                'response':response
            })
    return render(
        request, 'chatbot.html'
    )
