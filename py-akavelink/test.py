from pydantic import BaseModel
from typing import List

class BlogPost(BaseModel):
    id: int
    title: str
    content: str
    tags: list[str]
    published: bool = False

blogpost = BlogPost(id='4', title="hello", content="This is my blog post", tags=["blog", "post"], published=True)
print(blogpost)
