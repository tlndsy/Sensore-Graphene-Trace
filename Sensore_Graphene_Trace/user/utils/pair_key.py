import hashlib


def generate_pair_key(user1_id, user2_id):
    """
    Order-independent unique key for a pair of users.
    """
    sorted_ids = sorted([user1_id, user2_id])
    raw = f"{sorted_ids[0]}:{sorted_ids[1]}"
    return hashlib.sha256(raw.encode()).hexdigest()