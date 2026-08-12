import uuid
from datetime import datetime, timezone
from typing import Any

from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization, OrganizationMember, Invitation
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.comment import Comment

class BaseDBFactory(SQLAlchemyFactory[Any]):
    __is_base_factory__ = True
    
    @classmethod
    def set_session(cls, session: Session):
        cls.__set_session__(session)

class UserFactory(BaseDBFactory[User]):
    __model__ = User

class OrganizationFactory(BaseDBFactory[Organization]):
    __model__ = Organization

class OrganizationMemberFactory(BaseDBFactory[OrganizationMember]):
    __model__ = OrganizationMember

class InvitationFactory(BaseDBFactory[Invitation]):
    __model__ = Invitation

class ProjectFactory(BaseDBFactory[Project]):
    __model__ = Project

class ProjectMemberFactory(BaseDBFactory[ProjectMember]):
    __model__ = ProjectMember

class TaskFactory(BaseDBFactory[Task]):
    __model__ = Task

class CommentFactory(BaseDBFactory[Comment]):
    __model__ = Comment
