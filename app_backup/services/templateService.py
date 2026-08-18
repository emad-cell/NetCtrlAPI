from app.core.exceptions import GNS3RequestException, TemplateNotFoundException
from app.services.Gns3.Templates import (
    get_templates as get_gns3_templates,
    get_template as get_gns3_template,
)
from app.services.topologyRender import render_topology_image


########################## List Templates ##########################
async def get_templates() -> list[dict]:

    return await get_gns3_templates()
######################################################################

########################## Get Template #############################
async def get_template(
    template_id: str,
) -> dict:

    try:
        return await get_gns3_template(
            template_id=template_id,
        )
    except GNS3RequestException as e:
        if e.status_code == 404:
            raise TemplateNotFoundException("Template not found")
        raise
######################################################################

