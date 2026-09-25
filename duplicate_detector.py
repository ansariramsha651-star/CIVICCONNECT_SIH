from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def find_duplicate(new_description, existing_complaints):

    if not existing_complaints:
        return None, 0

    descriptions = [
        complaint.description
        for complaint in existing_complaints
    ]

    descriptions.append(new_description)

    vectorizer = TfidfVectorizer()

    vectors = vectorizer.fit_transform(descriptions)

    similarities = cosine_similarity(
        vectors[-1],
        vectors[:-1]
    )[0]

    highest_similarity = max(similarities)

    index = similarities.argmax()

    if highest_similarity >= 0.5:

        duplicate_complaint = existing_complaints[index]

        return duplicate_complaint, highest_similarity

    return None, highest_similarity