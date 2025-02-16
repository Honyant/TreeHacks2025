import weaviate
import voyageai
import os
import io
import PIL.Image
import base64
from typing import List, Dict
from dotenv import load_dotenv

from weaviate.classes.config import Configure
from weaviate.classes.query import MetadataQuery
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_from_base64_gzipped_json

load_dotenv()

def setup_db():
    client = weaviate.connect_to_local()
    collection_name = "demo"
    client.collections.delete(collection_name)

    try:
        client.collections.create(
            name=collection_name,
            vectorizer_config=Configure.Vectorizer.none()
        )
        collection = client.collections.get(collection_name)
    except Exception:
        collection = client.collections.get(collection_name)

    return client, collection

def load_pdfs(dir) -> List[Dict]:
    """
    Load all PDFs from the directory using Unstructured.
    Returns list of document elements.
    """
    documents = []
    for filename in os.listdir(dir):
        if filename.endswith('.pdf'):
            file_path = os.path.join(dir, filename)
            elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",
                extract_image_block_types=["Image", "Table"],
                extract_image_block_to_payload=True,
            )
            documents.extend(elements)
    return documents

def preprocess_chunks(elements):
    embedding_objects = []
    embedding_metadatas = []
    chunks = chunk_by_title(elements)

    for chunk in chunks:
        embedding_object = []
        metedata_dict = {
            "text": chunk.to_dict()["text"],
            "filename": chunk.to_dict()["metadata"]["filename"],
            "page_number": chunk.to_dict()["metadata"]["page_number"],
            "last_modified": chunk.to_dict()["metadata"]["last_modified"],
            "languages": chunk.to_dict()["metadata"]["languages"],
            "filetype": chunk.to_dict()["metadata"]["filetype"]
        }
        embedding_object.append(chunk.to_dict()["text"])

        # Add the images to the embedding object
        if "orig_elements" in chunk.to_dict()["metadata"]:
            base64_elements_str = chunk.to_dict()["metadata"]["orig_elements"]
            eles = elements_from_base64_gzipped_json(base64_elements_str)
            image_data = []
            for ele in eles:
                if ele.to_dict()["type"] == "Image":
                    base64_image = ele.to_dict()["metadata"]["image_base64"]
                    image_data.append(base64_image)
                    pil_image = PIL.Image.open(io.BytesIO(base64.b64decode(base64_image)))
                    # Resize image if larger than 1000x1000 while maintaining aspect ratio
                    if pil_image.size[0] > 1000 or pil_image.size[1] > 1000:
                        ratio = min(1000/pil_image.size[0], 1000/pil_image.size[1])
                        new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
                        pil_image = pil_image.resize(new_size, PIL.Image.Resampling.LANCZOS)
                    embedding_object.append(pil_image)

            metedata_dict["image_data"] = image_data

        embedding_objects.append(embedding_object)
        embedding_metadatas.append(metedata_dict)
    return embedding_objects, embedding_metadatas

def embed_data(embedding_objects, embedding_metadatas, collection):
    vo = voyageai.Client()
    result = vo.multimodal_embed(embedding_objects, model="voyage-multimodal-3", truncation=False)
    with collection.batch.dynamic() as batch:
        for i, data_row in enumerate(embedding_objects):
            batch.add_object(
                properties=embedding_metadatas[i],
                vector=result.embeddings[i]
            )

def query(question, collection):
    vo = voyageai.Client()
    query_embedding = vo.multimodal_embed([[question]], model="voyage-multimodal-3", truncation=False)
    response = collection.query.near_vector(
        near_vector=query_embedding.embeddings[0],
        limit=5,
        return_metadata=MetadataQuery(distance=True)
    )
    for o in response.objects:
        print(o.properties['text'])
        for image_data in o.properties['image_data']:
            # Display the image using PIL
            img = PIL.Image.open(io.BytesIO(base64.b64decode(image_data)))
            width, height = img.size
            if width > 500 or height > 500:
                ratio = min(500/width, 500/height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size)
            img.show()
        print(o.metadata.distance)

if __name__ == "__main__":
    client, collection = setup_db()
    elements = load_pdfs("./pdfs")
    embedding_objects, embedding_metadatas = preprocess_chunks(elements)
    embed_data(embedding_objects, embedding_metadatas, collection)
    query("Argentina", collection)
    breakpoint()