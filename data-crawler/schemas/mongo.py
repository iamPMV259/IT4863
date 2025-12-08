from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field


class PoemMetadata(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the poem")
    url: str = Field(..., description="URL of the poem page")
    tieuDe: str | None = Field(None, description="Title of the poem")
    tacGia: str | None = Field(None, description="Author of the poem")
    theTho: str | None = Field(None, description="Type of the poem")
    thoiKy: str | None = Field(None, description="Era of the poem")
    noiDungText: str | None = Field(None, description="Plain text content of the poem")
    noiDungHTML: str | None = Field(None, description="HTML content of the poem")
    tapTho: str | None = Field(None, description="Collection the poem belongs to")
    
    class Setting:
        name = "poem_metadata"
        validate_on_save = True
        indexs = [
            "tacGia",
            "theTho",
            "thoiKy",
        ]


class PoemInfo(BaseModel):
    tenBaiTho: str | None = Field(None, description="Title of the poem")
    url: str = Field(..., description="URL of the poem")

class AuthorMetadata(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the author")
    ten: str | None = Field(None, description="Name of the author")
    tenThat: str | None = Field(None, description="Real name of the author")
    url: str = Field(..., description="URL of the author's page")
    danhSachBaiTho: list[PoemInfo] = Field(default_factory=list, description="List of poems by the author")

    class Setting:
        name = "author_metadata"
        validate_on_save = True
        indexs = [
            "ten",
        ]



DocumentModels = [PoemMetadata, AuthorMetadata]
