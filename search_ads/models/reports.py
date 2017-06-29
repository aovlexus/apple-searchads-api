from datetime import datetime

import copy
import pandas as pd

from search_ads.api.utils import api_post


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def get_campaign_adgroups_report(campaign,
                                 org_id=None,
                                 start_time=_today(),
                                 end_time=_today(),
                                 timezone='UTC',
                                 granularity='HOURLY',
                                 selector=None,
                                 group_by=[],
                                 return_records_with_no_metrics=True,
                                 return_row_totals=False):
    return _report(
        campaign,
        path='adgroups',
        org_id=org_id,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone,
        granularity=granularity,
        selector=selector,
        group_by=group_by,
        return_records_with_no_metrics=return_records_with_no_metrics,
        return_row_totals=return_row_totals
    )


def get_campaign_searchterms_report(campaign,
                                    org_id=None,
                                    start_time=_today(),
                                    end_time=_today(),
                                    timezone='UTC',
                                    granularity='HOURLY',
                                    selector=None,
                                    group_by=[],
                                    return_records_with_no_metrics=True,
                                    return_row_totals=False):
    return _report(
        campaign,
        path='searchterms',
        org_id=org_id,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone,
        granularity=granularity,
        selector=selector,
        group_by=group_by,
        return_records_with_no_metrics=return_records_with_no_metrics,
        return_row_totals=return_row_totals
    )


def get_campaign_keywords_report(campaign,
                                 org_id=None,
                                 start_time=_today(),
                                 end_time=_today(),
                                 timezone='UTC',
                                 granularity='HOURLY',
                                 selector=None,
                                 group_by=[],
                                 return_records_with_no_metrics=True,
                                 return_row_totals=False):
    return _report(
        campaign,
        path='keywords',
        org_id=org_id,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone,
        granularity=granularity,
        selector=selector,
        group_by=group_by,
        return_records_with_no_metrics=return_records_with_no_metrics,
        return_row_totals=return_row_totals
    )


def get_campaign_report(org_id=None,
                        start_time=_today(),
                        end_time=_today(),
                        timezone='UTC',
                        granularity='HOURLY',
                        selector=None,
                        group_by=[],
                        return_records_with_no_metrics=True,
                        return_row_totals=False):
    return _report(
        path='',
        org_id=org_id,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone,
        granularity=granularity,
        selector=selector,
        group_by=group_by,
        return_records_with_no_metrics=return_records_with_no_metrics,
        return_row_totals=return_row_totals
    )


def _report(campaign=None,
            path='',
            org_id=None,
            start_time=_today(),
            end_time=_today(),
            timezone='UTC',
            granularity='HOURLY',
            selector=None,
            group_by=[],
            return_records_with_no_metrics=True,
            return_row_totals=False):
    if not selector:
        selector = {
            "orderBy": [
                {"field": "modificationTime", "sortOrder": "DESCENDING"}
            ],
            "conditions": [],
            "pagination": {"offset": 0, "limit": 1000}
        }

    data = {
        'startTime': start_time,
        'endTime': end_time,
        'timeZone': timezone,
        'granularity': granularity,
        'selector': selector,
        'groupBy': group_by,
        'returnRowTotals': return_row_totals,
        'returnRecordsWithNoMetrics': return_records_with_no_metrics
    }
    if campaign:
        url = "reports/campaigns/%s/%s" % (campaign._id, path)
    else:
        url = "reports/campaigns"
    output = []
    api_res = api_post(url, org_id=org_id, data=data)
    try:
        res = api_res['data']['reportingDataResponse']['row']
    except:
        raise Exception(api_res)  # ['data']['error']['errors'])
    for row in res:
        base = {}
        base.update(row['metadata'])
        if return_row_totals:
            base.update(row['total'])
        if campaign:
            base['adamId'] = campaign._adam_id
            base['campaignId'] = campaign._id
        else:
            base['adamId'] = base['app']['adamId']
            base['appName'] = base['app']['appName']
            del base['app']
        for granularity in row['granularity']:
            final_row = copy.copy(base)
            final_row.update(granularity)
            output.append(convert_to_float_all_amounts_in_row(final_row))
    return pd.DataFrame(output)


def amount_to_float(amount):
    return float(amount['amount'])


def convert_to_float_all_amounts_in_row(row):
    _row = copy.copy(row)
    for field_name, value in _row.items():
        if isinstance(value, dict) and 'currency' in value:
            _row[field_name] = amount_to_float(value)
    return _row
