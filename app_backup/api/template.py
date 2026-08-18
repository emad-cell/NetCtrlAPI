from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.exceptions import TemplateNotFoundException
from app.models.user import User
from app.schemas.template import TemplateResponse
from app.services import templateService

router = APIRouter(
    prefix="/templates",
    tags=["Templates"],
)


########################## List Templates ##########################
@router.get(
    "",
    response_model=list[TemplateResponse],
)
async def list_templates(
    current_user: User = Depends(get_current_user),
):
    return await templateService.get_templates()
######################################################################

########################## Get Template #############################
@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        return await templateService.get_template(
            template_id=template_id,
        )
    except TemplateNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
######################################################################