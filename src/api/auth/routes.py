from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.core.logging import logger
from src.core.security import create_access_token, hash_password, verify_password
from src.crud.user import create_user, get_user_by_email
from src.models.user import User
from src.schemas.auth import LoginRequest, Token
from src.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """Register a new caregiver or admin user."""
    existing_user = get_user_by_email(db, user_data.email, include_deleted=True)
    if existing_user:
        logger.warning(
            "Registration rejected: email %s already exists", user_data.email
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists",
        )

    # Securely hash password before persistence
    hashed_pwd = hash_password(user_data.password)
    new_user = create_user(db, user_data=user_data, password_hash=hashed_pwd)
    logger.info("User registered successfully with ID %s", new_user.id)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="OAuth2 compatible token login (form data)",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """OAuth2 password request form login (used by Swagger UI and standard OAuth2 clients).

    The 'username' form field must contain the user's email address.
    """
    user = get_user_by_email(db, form_data.username, include_deleted=False)
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(
            "Failed login attempt for username/email: %s", form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )
    logger.info("User %s logged in successfully", user.id)
    return Token(access_token=token, token_type="bearer")


@router.post(
    "/login/json",
    response_model=Token,
    summary="JSON body login for REST API clients",
)
def login_json(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate via JSON payload and receive a JWT access token."""
    user = get_user_by_email(db, credentials.email, include_deleted=False)
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(
            "Failed JSON login attempt for email: %s", credentials.email
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )
    logger.info("User %s logged in successfully via JSON", user.id)
    return Token(access_token=token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Retrieve details of the currently authenticated user."""
    return current_user
