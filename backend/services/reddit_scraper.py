"""
KnowledgeTree - Reddit Scraper Service
Uses PRAW (Python Reddit API Wrapper) for official API access
"""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class RedditPost:
    """Reddit post data"""
    id: str
    title: str
    author: str
    subreddit: str
    score: int
    upvote_ratio: float
    num_comments: int
    url: str
    permalink: str
    created_utc: float
    selftext: str
    is_self: bool
    link_flair_text: Optional[str]


@dataclass
class RedditSubreddit:
    """Subreddit info"""
    name: str
    title: str
    description: str
    subscribers: int
    active_users: int
    created_utc: float
    over18: bool
    url: str


@dataclass
class RedditScraperResult:
    """Result from Reddit scraping"""
    source: str  # "api" or "playwright"
    url: str
    title: str
    content: str
    posts: List[Dict[str, Any]]
    subreddit_info: Optional[Dict[str, Any]]
    error: Optional[str] = None


class RedditScraper:
    """
    Reddit scraper using PRAW (official API)
    
    Pros:
    - Official API access
    - No rate limit issues for read-only
    - No login required for public content
    - Well-structured data
    
    Cons:
    - Requires API credentials (free from reddit.com/prefs/apps)
    - Limited to 1000 posts per request
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "KnowledgeTree/1.0"
    ):
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent
        
        # Lazy import - only if credentials available
        self._reddit = None
        self._praw_available = False
        
        if self.client_id and self.client_secret:
            try:
                import praw
                self._reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                    read_only=True
                )
                self._praw_available = True
            except ImportError:
                pass
    
    @property
    def available(self) -> bool:
        """Check if PRAW is available"""
        return self._praw_available
    
    async def scrape_subreddit(
        self,
        subreddit_name: str,
        limit: int = 50,
        sort: str = "hot"  # hot, new, top, rising
    ) -> RedditScraperResult:
        """
        Scrape a subreddit
        
        Args:
            subreddit_name: Name of subreddit (without r/)
            limit: Number of posts to fetch (max 100)
            sort: Sort order (hot, new, top, rising)
        
        Returns:
            RedditScraperResult with posts and subreddit info
        """
        if not self.available:
            return RedditScraperResult(
                source="api",
                url=f"https://www.reddit.com/r/{subreddit_name}/",
                title="",
                content="",
                posts=[],
                subreddit_info=None,
                error="Reddit API credentials not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET."
            )
        
        try:
            import praw
            
            # Get subreddit
            subreddit = self._reddit.subreddit(subreddit_name)
            
            # Fetch posts based on sort
            if sort == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort == "new":
                posts = subreddit.new(limit=limit)
            elif sort == "top":
                posts = subreddit.top(limit=limit)
            elif sort == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                posts = subreddit.hot(limit=limit)
            
            # Convert to list and extract data
            posts_data = []
            for post in posts:
                posts_data.append({
                    "id": post.id,
                    "title": post.title,
                    "author": str(post.author) if post.author else "[deleted]",
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": f"https://www.reddit.com{post.permalink}",
                    "created_utc": post.created_utc,
                    "selftext": post.selftext if post.is_self else "",
                    "is_self": post.is_self,
                    "link_flair_text": post.link_flair_text,
                    "over_18": post.over_18
                })
            
            # Get subreddit info
            try:
                sub_info = {
                    "name": subreddit.display_name,
                    "title": subreddit.title,
                    "description": subreddit.description[:500] if subreddit.description else "",
                    "subscribers": subreddit.subscribers,
                    "active_users": subreddit.active_user_count,
                    "created_utc": subreddit.created_utc,
                    "over18": subreddit.over18,
                    "url": f"https://www.reddit.com/r/{subreddit_name}/"
                }
            except:
                sub_info = None
            
            # Build content text
            content_parts = [
                f"Subreddit: r/{subreddit_name}",
                f"Posts fetched: {len(posts_data)}",
                ""
            ]
            
            for i, post in enumerate(posts_data[:10], 1):
                content_parts.extend([
                    f"{i}. {post['title']}",
                    f"   Score: {post['score']} | Comments: {post['num_comments']}",
                    f"   URL: {post['url']}",
                    ""
                ])
            
            return RedditScraperResult(
                source="api",
                url=f"https://www.reddit.com/r/{subreddit_name}/",
                title=f"r/{subreddit_name}",
                content="\n".join(content_parts),
                posts=posts_data,
                subreddit_info=sub_info,
                error=None
            )
        
        except Exception as e:
            return RedditScraperResult(
                source="api",
                url=f"https://www.reddit.com/r/{subreddit_name}/",
                title="",
                content="",
                posts=[],
                subreddit_info=None,
                error=f"Reddit API error: {str(e)}"
            )
    
    async def scrape_post(
        self,
        post_id: str
    ) -> RedditScraperResult:
        """
        Scrape a single Reddit post
        
        Args:
            post_id: Reddit post ID (e.g., "14g5h6k")
        
        Returns:
            RedditScraperResult with post data and comments
        """
        if not self.available:
            return RedditScraperResult(
                source="api",
                url=f"https://www.reddit.com/comments/{post_id}/",
                title="",
                content="",
                posts=[],
                subreddit_info=None,
                error="Reddit API credentials not configured"
            )
        
        try:
            import praw
            
            submission = self._reddit.submission(id=post_id)
            
            # Force load comments
            submission.comments.replace_more(limit=0)
            
            # Extract comments
            comments_data = []
            for comment in submission.comments.list()[:50]:  # Top 50 comments
                if hasattr(comment, 'body'):
                    comments_data.append({
                        "author": str(comment.author) if comment.author else "[deleted]",
                        "body": comment.body[:500],  # Limit length
                        "score": comment.score,
                        "created_utc": comment.created_utc
                    })
            
            # Build content
            content_parts = [
                f"Title: {submission.title}",
                f"Author: {submission.author}",
                f"Score: {submission.score}",
                f"Comments: {submission.num_comments}",
                "",
                "Self text:",
                submission.selftext if submission.is_self else "[Link post]",
                "",
                f"Link: {submission.url}",
                "",
                "Top comments:",
            ]
            
            for i, comment in enumerate(comments_data[:20], 1):
                content_parts.extend([
                    f"{i}. {comment['author']} ({comment['score']} pts)",
                    f"   {comment['body'][:200]}",
                    ""
                ])
            
            return RedditScraperResult(
                source="api",
                url=f"https://www.reddit.com/comments/{post_id}/",
                title=submission.title,
                content="\n".join(content_parts),
                posts=[{
                    "id": submission.id,
                    "title": submission.title,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "url": submission.url,
                    "selftext": submission.selftext if submission.is_self else "",
                    "comments": comments_data
                }],
                subreddit_info=None,
                error=None
            )
        
        except Exception as e:
            return RedditScraperResult(
                source="api",
                url=f"https://www.reddit.com/comments/{post_id}/",
                title="",
                content="",
                posts=[],
                subreddit_info=None,
                error=f"Reddit API error: {str(e)}"
            )
    
    async def search(
        self,
        query: str,
        subreddit: Optional[str] = None,
        limit: int = 50,
        sort: str = "relevance"  # relevance, hot, top, new, comments
    ) -> RedditScraperResult:
        """
        Search Reddit
        
        Args:
            query: Search query
            subreddit: Limit search to subreddit (optional)
            limit: Number of results
            sort: Sort order
        
        Returns:
            RedditScraperResult with search results
        """
        if not self.available:
            return RedditScraperResult(
                source="api",
                url="",
                title="",
                content="",
                posts=[],
                subreddit_info=None,
                error="Reddit API credentials not configured"
            )
        
        try:
            import praw
            
            # Perform search
            if subreddit:
                results = self._reddit.subreddit(subreddit).search(
                    query, 
                    limit=limit,
                    sort=sort
                )
                url = f"https://www.reddit.com/r/{subreddit}/search?q={query}"
            else:
                results = self._reddit.subreddit("all").search(
                    query,
                    limit=limit,
                    sort=sort
                )
                url = f"https://www.reddit.com/search?q={query}"
            
            # Extract results
            posts_data = []
            for post in results:
                posts_data.append({
                    "id": post.id,
                    "title": post.title,
                    "author": str(post.author) if post.author else "[deleted]",
                    "subreddit": str(post.subreddit),
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": f"https://www.reddit.com{post.permalink}",
                    "selftext": post.selftext[:500] if post.is_self else "",
                    "is_self": post.is_self
                })
            
            # Build content
            content_parts = [
                f"Search: {query}",
                f"Results: {len(posts_data)} posts",
                ""
            ]
            
            for i, post in enumerate(posts_data[:20], 1):
                content_parts.extend([
                    f"{i}. {post['title']}",
                    f"   r/{post['subreddit']} | {post['score']} pts | {post['num_comments']} comments",
                    f"   {post['url']}",
                    ""
                ])
            
            return RedditScraperResult(
                source="api",
                url=url,
                title=f"Search: {query}",
                content="\n".join(content_parts),
                posts=posts_data,
                subreddit_info=None,
                error=None
            )
        
        except Exception as e:
            return RedditScraperResult(
                source="api",
                url="",
                title="",
                content="",
                posts=[],
                subreddit_info=None,
                error=f"Reddit search error: {str(e)}"
            )


# Singleton instance
reddit_scraper = RedditScraper()
