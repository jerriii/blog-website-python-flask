import math


def cosine_similarity(vec1, vec2):
    sum_vec1 = 0
    sum_vec2 = 0
    sum_product = 0

    for i, j in zip(vec1, vec2):
        i = ord(i)
        j = ord(j)
        sum_vec1 += i**2
        sum_vec2 += j**2
        sum_product += i*j

    return sum_product / (math.sqrt(sum_vec1) * math.sqrt(sum_vec2))


def recommend_post(user, post_list):
    posts = {}

    if not user:
        return post_list

    user_topics = user.topics.split(',')

    for post in post_list:
        point = 0

        # Content similarity based on user's time spent
        for time_spent in user.time_spent:
            point += cosine_similarity(time_spent.post.content, post.content) * time_spent.time
            point *= 0.5 if time_spent.post == post else 1.5

        for topic in user_topics:
            point += 40 * (topic in post.title)
            point += 6 * min(post.content.lower().count(topic.lower()), 5)

        point += 60 * (post.content_type == user.preferences)

        point += 0.01 * min(len(post.content), 10_000)

        point += 5 * post.overall_rating * len(post.ratings)

        point += 0.02 * (post.date.day + post.date.month * 1.2 + post.date.year * 1.5)

        posts[post] = point

    max_point = max(posts.values())
    posts = {post: point / max_point for post, point in posts.items()}

    return list(dict(sorted(posts.items(), key=lambda item: -item[1])).keys())


# def recommend_post(user, post_list):
#     posts = {}
#     if not user:
#         return post_list
#     for post in post_list:
#         point = 0
#         for time_spent in user.time_spent:
#             point += cosine_similarity(time_spent.post.content,  post.content) *time_spent.time
#             point *= 0.5 if time_spent.post == post else 1.5
#         for topic in user.topics.split(','):
#             point += 40 * (topic in post.title)
#             point += 6 * min(post.content.count(topic), 5)
#         point += 60 * post.content_type == user.preferences
#         point += 0.01 * min(len(post.content), 10_000)
#         point += 5 * post.overall_rating * len(post.ratings)
#         point += 0.02 * (post.date.day + post.date.month*1.2 + post.date.year * 1.5)
#         posts[post] = point
#     return list(dict(sorted(posts.items(), key=lambda item: -item[1])).keys())


