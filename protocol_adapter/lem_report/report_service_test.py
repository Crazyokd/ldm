import time
import logging

from protocol_adapter.lem_report.models_payload import AlarmData, AutoCheckData
from protocol_adapter.lem_report.models import (
    ApiInfo,
    DeployInfo,
    ReportType,
    ReportServiceConfig,
    ReportTaskSpec,
)
from protocol_adapter.lem_report.service import ReportTask, ReportService
from protocol_adapter.mock.rest_api_mock import ApiConfig

logger = logging.getLogger(__name__)


def status_data_callback():
    """模拟心跳数据采集"""
    return {
        'device_code': 'AGV001',
        'status': 1,
        'current_x': 100.0,
        'current_y': 200.0,
        'current_h': 50.0,
        'current_speed': 10.0,
        'battery_level': 80,
    }


def alarm_data_callback():
    """模拟告警数据采集"""
    return None


def test_report_service(mock_api_server: ApiConfig):
    config = ReportServiceConfig(
        api_info=ApiInfo(
            url=mock_api_server.url,
            app_id='id',
            app_key='key',
            topic='',
        ),
        deploy=DeployInfo(siteId='XT02'),
    )
    print(config)
    service = ReportService(config)
    service.start(wait_ready=True)

    # 添加状态上报任务
    measure_task = ReportTask(
        name='status',
        reporter_type=ReportType.AgvAutoCheck,
        interval_ms=123,
        max_count=20,
        callback=status_data_callback,
        spec=ReportTaskSpec(checkDatas=[AutoCheckData()]),
    )
    measure_task_id = service.add_task(measure_task)

    # 添加告警上报任务
    alarm_task = ReportTask(
        name='alarm',
        reporter_type=ReportType.AgvAlarm,
        interval_ms=220,
        callback=alarm_data_callback,
        spec=ReportTaskSpec(
            agv_id=1024,
            alarmData=AlarmData(
                alarmModule='1',
                mainTypeCode='02',
                minorTypeCode='002',
                mapCode='CC',
                alarmX=1.1,
                alarmY=2.2,
                parameter1='T1234321',
            ),
            end_on_collect=True,
            delay_ms=200,  # 延迟 200ms
        ),
    )
    service.add_task(alarm_task)

    # 添加告警上报任务
    alarm_task = ReportTask(
        name='alarm2',
        reporter_type=ReportType.AgvAlarm,
        interval_ms=600,
        callback=alarm_data_callback,
        spec=ReportTaskSpec(
            agv_id=1020,
            alarmData=AlarmData(
                alarmModule='1',
                mainTypeCode='02',
                minorTypeCode='401',
                mapCode='CA',
                alarmX=112,
                alarmY=222,
                parameter1='T1234321xx',
            ),
            end_at_timestamp=service.get_loop_ts() + 2,
        ),
    )
    service.add_task(alarm_task)

    # 运行一段时间后暂停任务

    if measure_task_id:
        time.sleep(1.2)
        logger.info('pause measure task ..')
        service.pause_task(measure_task_id)

    # 继续任务
    if measure_task_id:
        time.sleep(1.4)

    # 运行一段时间后暂停任务

    if measure_task_id:
        time.sleep(1.2)
        logger.info('pause measure task ..')
        service.pause_task(measure_task_id)

    # 继续任务
    if measure_task_id:
        time.sleep(1.4)
        logger.info('resume measure task ..')
        service.resume_task(measure_task_id)

    # 停止服务
    time.sleep(2.8)
    service.stop()
