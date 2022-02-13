from datetime import datetime
from re import T
from flask import render_template, session, redirect, url_for, request, current_app, abort, flash
from flask_login import current_user
from flask_sqlalchemy import Pagination
from sqlalchemy.sql import text
import bleach
from app.decorators import permission_required
from . import main
from .. import db
from ..models import *
from .forms import *

@main.route("/", methods=["GET","POST"])
def index():
    form = PostForm()
    tags = Tag.query.order_by(Tag.id).all()
    form.tagging.choices = [(tag.id, tag.name) for tag in tags]
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(header= form.header.data, body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        tagging = Tagging(post_id=post.id, tag1_id=form.tagging.data[0], tag2_id=form.tagging.data[1], tag3_id=form.tagging.data[2])
        db.session.add(tagging)
        db.session.commit()
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config["FLASKY_POSTS_PER_PAGE"], error_out=False)
    posts = pagination.items
    return render_template("index.html", post_submit_form=form, posts=posts, pagination=pagination)

@main.route("/post/<int:id>", methods=["GET", "POST"])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash("your comment has been sent")
        return redirect(url_for(".post", id=post.id, page=-1))
    page = request.args.get("page", 1, type=int)
    if page== -1:
        page = (post.comments.count() -1) // current_app.config["FLASKY_COMMENTS_PER_PAGE"] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).filter(Comment.disabled==False).paginate(page, per_page=current_app.config["FLASKY_COMMENTS_PER_PAGE"], error_out=False)

    comments = pagination.items
    return render_template("post.html", posts=[post], comment_form=form, comments= comments, pagination=pagination)

@main.route("/disable/<int:id>")
@permission_required(Permission.ADMIN)
def disable(id):
    comment = Comment.query.get_or_404(id)
    if not current_user.can(Permission.ADMIN):
        abort(403)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for(".post",id=comment.post_id))

@main.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if not current_user.can(Permission.ADMIN):
        abort(403)
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)

    form = PostForm()
    tags = Tag.query.order_by(Tag.id).all()
    form.tagging.choices = [(tag.id, tag.name) for tag in tags]
    
    if form.validate_on_submit():
        post.body = form.body.data
        post.header = form.header.data
        post.tagging.update(form.tagging.data)
        post.last_edited = datetime.utcnow()
        db.session.add(post)
        db.session.commit()
        flash("the post has been updated.")
        return redirect(url_for(".post", id=post.id))
    form.body.data = post.body
    form.header.data = post.header
    form.tagging.default = [post.tagging.tag1_id, post.tagging.tag2_id, post.tagging.tag3_id]
    form.tagging.data = [post.tagging.tag1_id, post.tagging.tag2_id, post.tagging.tag3_id]
    return render_template("edit_post.html", edit_form=form)

@main.route("/remove/<int:id>")
@permission_required(Permission.ADMIN)
def remove(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    db.session.delete(post.tagging)
    db.session.commit()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for(".index"))

@main.route("/posts", methods=["GET","POST"])
def posts():
    form = PostFilterForm()
    tags = Tag.query.order_by(Tag.id).all()
    form.tag.choices = [(tag.id, tag.name) for tag in tags]
    if form.validate_on_submit():
        time_order = Post.timestamp.asc() if form.time_order.data == 2 else Post.timestamp.desc()
        page = request.args.get("page", 1, type=int)
        search = bleach.clean(form.header.data)
        search = "%{}%".format(search)
        pagination = db.session.query(Post).join(Post.tagging).order_by(time_order) \
                                                .filter(Tagging.tag1_id==form.tag.data) \
                                                .filter(Post.header.like(search)) \
                                                .paginate(page, per_page=current_app.config["FLASKY_POSTS_PER_PAGE"], error_out=False)
        posts = pagination.items
        return render_template("posts.html", post_filter_form=form, posts=posts, pagination=pagination)

    page = request.args.get("page", 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config["FLASKY_POSTS_PER_PAGE"], error_out=False)
    posts = pagination.items
    return render_template("posts.html", post_filter_form=form, posts=posts, pagination=pagination)

@main.route("/aboutme")
def aboutme():
    return render_template("aboutme.html")

@main.route("/contact")
def contact():
    return render_template("contact.html")