from .custom_fastcrud import FastCRUDNoCommit

from ..models.post import Post
from ..schemas.post import PostCreateInternal, PostDelete, PostRead, PostUpdate, PostUpdateInternal

CRUDPost = FastCRUDNoCommit[Post, PostCreateInternal, PostUpdate, PostUpdateInternal, PostDelete, PostRead]
crud_posts = CRUDPost(Post)
