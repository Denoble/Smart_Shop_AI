from sentence_transformers import SentenceTransformer



class EmbeddingModel:

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return vector.tolist()
    

def product_to_text(product) -> str:
    return f"""
    Product: {product.name}
    Brand: {product.brand}
    Category: {product.category}

    Description:
    {product.description}

    Price:
    {product.price}

    """
    
def review_to_text(review) -> str:
    return f"""
    Product: {review.product_name}

    Rating:
    {review.rating}/5

    Review:
    {review.review_text}

    Sentiment:
    {review.sentiment}
    """
def policy_to_text(policy) -> str:
    return f"""
    Store: {policy.store_name}

    Policy Category:
    {policy.category}

    Type:
    {policy.policy_type}
    Policy:
    {policy.content}
    """
