from pydantic import BaseModel, Field


class TweakSettingsLoop(BaseModel):
    debug: bool = Field(default=False, description='enable event loop debug')
    slow_ms: int = Field(default=20, description='consider slow if task blocked')


class TweakSettingsReport(BaseModel):
    workers: int = Field(default=20, description='max report workers')
    queue_size: int = Field(default=1000, description='max report task that can be queued')


class TweakSettings(BaseModel):
    loop: TweakSettingsLoop = Field(default=TweakSettingsLoop())
    report: TweakSettingsReport = Field(default=TweakSettingsReport())
