from datetime import datetime
from uuid import UUID, uuid4
from pony.orm import *

from lib.models.mixins import *

from lib.config import config

db = Database()


class Platform(db.Entity, PlatformMixin):
    _table_ = "platforms"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    sub_platforms = Set("SubPlatform")
    products = Set("Product")
    users = Set("User")
    product_providers = Set('ProductProvider')


class SubPlatform(db.Entity, SubPlatformMixin):
    _table_ = "sub_platforms"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    platform = Required("Platform")
    products = Set("Product")


class Product(db.Entity, ProductMixin):
    _table_ = "products"
    uuid = PrimaryKey(UUID, default=uuid4)
    type = Required(unicode)
    name = Optional(unicode)
    external_id = Optional(unicode)
    description = Optional(LongUnicode)
    release_date = Optional(datetime)
    is_free_to_play = Optional(bool)
    is_visible = Optional(bool)
    review_label = Optional(unicode)
    review_total = Optional(int)
    review_positive = Optional(int)
    review_negative = Optional(int)
    platform = Required("Platform")
    sub_platforms = Set("SubPlatform")
    developers = Set("Developer")
    publishers = Set("Publisher")
    product_tags = Set("ProductTag")
    product_genres = Set("ProductGenre")
    product_categories = Set("ProductCategory")
    product_achievements = Set("ProductAchievement")
    product_images = Set("ProductImage")
    product_providers = Set('ProductProvider')
    created_at = Required(datetime, default=datetime.utcnow)
    updated_at = Required(datetime, default=datetime.utcnow)
    children = Set("Product", reverse="parent")
    parent = Optional("Product", reverse="children")
    playthroughs = Set("Playthrough")
    users = Set("User")



class Developer(db.Entity, DeveloperMixin):
    _table_ = "developers"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    products = Set("Product")


class Publisher(db.Entity, PublisherMixin):
    _table_ = "publishers"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    products = Set("Product")


class ProductTag(db.Entity, ProductTagMixin):
    _table_ = "product_tags"
    uuid = PrimaryKey(UUID, default=uuid4)
    label = Required(unicode)
    products = Set("Product")


class ProductGenre(db.Entity, ProductGenreMixin):
    _table_ = "product_genres"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    external_id = Optional(unicode)
    products = Set("Product")


class ProductCategory(db.Entity, ProductCategoryMixin):
    _table_ = "product_categories"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    external_id = Optional(unicode)
    products = Set("Product")


class ProductAchievement(db.Entity, ProductAchievementMixin):
    _table_ = "product_achievements"
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    external_id = Optional(unicode)
    description = Optional(LongUnicode)
    is_hidden = Optional(bool)
    icon_url = Optional(LongUnicode)
    icon_earned_url = Optional(LongUnicode)
    global_percent = Optional(float)
    product = Required("Product")
    created_at = Required(datetime, default=datetime.utcnow)
    updated_at = Required(datetime, default=datetime.utcnow)
    users = Set("User")


class ProductImage(db.Entity, ProductImageMixin):
    _table_ = "product_images"
    uuid = PrimaryKey(UUID, default=uuid4)
    type = Required(unicode)
    url = Required(LongUnicode)
    product = Required("Product")


class ProductProvider(db.Entity, ProductProviderMixin):
    _table_ = 'product_providers'
    uuid = PrimaryKey(UUID, default=uuid4)
    name = Required(unicode)
    url = Optional(LongUnicode)
    product_fetching_class = Required(unicode)
    platforms = Set("Platform")
    products = Set("Product")


class Playthrough(db.Entity, PlaythroughMixin):
    _table_ = "playthroughs"
    uuid = PrimaryKey(UUID, default=uuid4)
    product = Required("Product")
    playthrough_labels = Set("PlaythroughLabel")
    playthrough_objectives = Set("PlaythroughObjective")
    user = Required("User")
    playthrough_medias = Set("PlaythroughMedia")


class PlaythroughLabelCategory(db.Entity, PlaythroughLabelCategoryMixin):
    _table_ = "playthrough_label_categories"
    uuid = PrimaryKey(UUID, default=uuid4)
    playthrough_labels = Set("PlaythroughLabel")


class PlaythroughLabel(db.Entity, PlaythroughLabelMixin):
    _table_ = "playthrough_labels"
    uuid = PrimaryKey(UUID, default=uuid4)
    playthroughs = Set("Playthrough")
    playthrough_label_category = Required("PlaythroughLabelCategory")


class PlaythroughObjective(db.Entity, PlaythroughObjectiveMixin):
    _table_ = "playthrough_objectives"
    uuid = PrimaryKey(UUID, default=uuid4)
    playthroughs = Set("Playthrough")


class PlaythroughMedia(db.Entity, PlaythroughMediaMixin):
    _table_ = "playthrough_medias"
    uuid = PrimaryKey(UUID, default=uuid4)
    type = Required(unicode)
    provider = Required(unicode)
    url = Required(LongUnicode)
    playthrough = Required("Playthrough")


class User(db.Entity, UserMixin):
    _table_ = "users"
    uuid = PrimaryKey(UUID, default=uuid4)
    platforms = Set("Platform")
    products = Set("Product")
    product_achievements = Set("ProductAchievement")
    playthroughs = Set("Playthrough")


try:
    db.bind(
        "postgres",
        user=config["database"]["user"],
        password=config["database"]["password"],
        host=config["database"]["host"],
        database=config["database"]["name"]
    )

    db.generate_mapping(create_tables=True)
except Exception as e:
    print(e)


