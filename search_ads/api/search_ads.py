import json
from datetime import datetime, timedelta

import pandas as pd
from tqdm import tqdm

from search_ads.api.utils import api_get
from search_ads.models.store_models import Campaign, AdGroup
from search_ads.models.reports import _today, \
    get_campaign_report as _get_campaign_report, \
    get_campaign_keywords_report as _get_campaign_keywords_report, \
    get_campaign_searchterms_report as _get_campaign_searchterms_report, \
    get_campaign_adgroups_report as _get_campaign_adgroups_report

class DataBase(object):
    campaigns = []
    reports = {}

    def serialize_database(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def restore_database(json_data):
        return DataBase(**json.loads(json_data))


class SearchAds(object):
    def __init__(self, org_name, api_version='v1'):
        """
        Initialize the API object
        :param org_name: Your organization name as found in the SearchAds interface
        :param api_version: The API version (current is v1)
        """
        self.api_version = api_version
        orgs = api_get("acls", api_version=self.api_version)
        self.org_id = None
        for org in orgs['data']:
            if org['orgName'] == org_name:
                self.org_id = org['orgId']
        if not self.org_id:
            raise Exception(
                "Organization %s does not exist on this account" % org_name)

    def _call(self, endpoint, verbose=False):
        return \
            api_get(endpoint, org_id=self.org_id, api_version=self.api_version,
                    verbose=verbose)['data']

    def store_campaigns(self, database):
        for campaign in self.get_campaigns():
            database.campaigns.append(campaign.to_json())

    def store_reports(self, campaigns, database, granularity=None,
                      start_date=None, end_date=None):
        _start_date, _end_date, _granularity = start_date, end_date, granularity
        for campaign in tqdm(campaigns):
            database.reports[campaign] = {}
            for report, func in [
                ('keywords', self.get_campaign_keywords_report),
                ('searchterms', self.get_campaign_searchterms_report),
                ('adgroup', self.get_campaign_adgroups_report),
                ('campaign', self.get_campaign_report)
            ]:
                start_date = _start_date or (datetime.now() - timedelta(days=30))
                end_date = _end_date or datetime.now()
                granularity = _granularity or 'HOURLY'
                if report == 'searchterms' and granularity == 'HOURLY':
                    # "Warning: forcing daily granularity for search terms"
                    granularity = 'DAILY'
                step = {
                    'HOURLY': 7,
                    'DAILY': 90,
                    'WEEKLY': 365
                }[granularity]

                selector = {
                    "orderBy": [
                        {
                            "field": "impressions",
                            "sortOrder": "DESCENDING"
                        }
                    ],
                    "pagination": {
                        "offset": 0, "limit": 5000
                    }
                }
                dfs = []
                while start_date < end_date:
                    if report != 'campaign':
                        tdf = func(
                            campaign=campaign,
                            start_time=start_date.strftime("%Y-%m-%d"),
                            end_time=(start_date + timedelta(days=step)).strftime(
                                "%Y-%m-%d"),
                            granularity=granularity,
                            return_records_with_no_metrics=False,
                            return_row_totals=False,
                            selector=selector
                        )
                    else:
                        tdf = func(
                            start_time=start_date.strftime("%Y-%m-%d"),
                            end_time=(start_date + timedelta(days=step)).strftime(
                                "%Y-%m-%d"),
                            granularity=granularity,
                            return_records_with_no_metrics=False,
                            return_row_totals=False,
                            selector=selector
                        )
                    start_date += timedelta(days=step)
                    dfs.append(tdf)
                if report != 'campaign':
                    database.reports[campaign][report] = pd.concat(
                        dfs) if dfs else []
                else:
                    database.reports[report] = pd.concat(
                        dfs) if dfs else []

    def get_campaigns(self, limit=2000):
        """
        Return all campaigns in the account
        :param limit: limit the results (default is 2000)
        :return: a list of Campaign objects
        """
        campaigns = []
        data = \
            api_get('campaigns', org_id=self.org_id,
                    api_version=self.api_version,
                    limit=limit)['data']
        for raw_campaign in data:
            campaigns.append(Campaign(**raw_campaign))
        return campaigns

    def get_campaigns_by_name(self, name):
        """
        Fetches all campaigns that match a certain name
        :param name: the query for the name
        :return: a list of Campaign objects
        """
        campaigns = []
        """
        # Unfortunately apple doesn't document the parameters for /find (...)
        data = \
            api_post('campaigns/find', org_id=self.org_id,
                api_version=self.api_version, data=name)['data']
        for raw_campaign in data:
            campaigns.append(Campaign(**raw_campaign))
        return campaigns
        """
        for campaign in self.get_campaigns():
            if name.lower() in campaign.name.lower():
                campaigns.append(campaign)
        return campaigns

    def get_campaign_keywords_report(self,
                                     campaign,
                                     start_time=_today(),
                                     end_time=_today(),
                                     timezone='UTC',
                                     granularity='HOURLY',
                                     selector=None,
                                     group_by=[],
                                     return_records_with_no_metrics=True,
                                     return_row_totals=False):
        """
        Retrieve a Campaign All Keyword report from Apple and returns it as a Pandas DataFrame
        :param campaign: a Campaign object
        :param start_time: a string (yyyy-mm-dd), start time
        :param end_time:  a string (yyyy-mm-dd), end time
        :param timezone: UTC or ORTZ
        :param granularity: 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY'
        :param selector: an object with keys {conditions, fields, orderBy, pagination: # of results, default 20}
        :param group_by: field to group by
        :param return_row_totals: whether to return row totals or not
        :param return_records_with_no_metrics: whether to return zero rows or not
        :return: Pandas DataFrame containing the report
        """
        return _get_campaign_keywords_report(
            org_id=self.org_id,
            campaign=campaign,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            granularity=granularity,
            selector=selector,
            group_by=group_by,
            return_records_with_no_metrics=return_records_with_no_metrics,
            return_row_totals=return_row_totals
        )

    def get_campaign_searchterms_report(self,
                                        campaign,
                                        start_time=_today(),
                                        end_time=_today(),
                                        timezone='UTC',
                                        granularity='HOURLY',
                                        selector=None,
                                        group_by=[],
                                        return_records_with_no_metrics=True,
                                        return_row_totals=False):
        """
        Retrieve a Campaign Search Terms report from Apple and returns it as a Pandas DataFrame
        :param campaign: a Campaign object
        :param start_time: a string (yyyy-mm-dd), start time
        :param end_time:  a string (yyyy-mm-dd), end time
        :param timezone: UTC or ORTZ
        :param granularity: 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY'
        :param selector: an object with keys {conditions, fields, orderBy, pagination: # of results, default 20}
        :param group_by: field to group by
        :param return_row_totals: whether to return row totals or not
        :param return_records_with_no_metrics: whether to return zero rows or not
        :return: Pandas DataFrame containing the report
        """
        return _get_campaign_searchterms_report(
            org_id=self.org_id,
            campaign=campaign,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            granularity=granularity,
            selector=selector,
            group_by=group_by,
            return_records_with_no_metrics=return_records_with_no_metrics,
            return_row_totals=return_row_totals
        )

    def get_campaign_adgroups_report(self,
                                     campaign,
                                     start_time=_today(),
                                     end_time=_today(),
                                     timezone='UTC',
                                     granularity='HOURLY',
                                     selector=None,
                                     group_by=[],
                                     return_records_with_no_metrics=True,
                                     return_row_totals=False):
        """
        Retrieve a Campaign Ad Groups report from Apple and returns it as a Pandas DataFrame
        :param campaign: a Campaign object
        :param start_time: a string (yyyy-mm-dd), start time
        :param end_time:  a string (yyyy-mm-dd), end time
        :param timezone: UTC or ORTZ
        :param granularity: 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY'
        :param selector: an object with keys {conditions, fields, orderBy, pagination: # of results, default 20}
        :param group_by: field to group by
        :param return_row_totals: whether to return row totals or not
        :param return_records_with_no_metrics: whether to return zero rows or not
        :return: Pandas DataFrame containing the report
        """
        return _get_campaign_adgroups_report(
            org_id=self.org_id,
            campaign=campaign,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            granularity=granularity,
            selector=selector,
            group_by=group_by,
            return_records_with_no_metrics=return_records_with_no_metrics,
            return_row_totals=return_row_totals
        )

    def get_campaign_report(self,
                            start_time=_today(),
                            end_time=_today(),
                            timezone='UTC',
                            granularity='HOURLY',
                            selector=None,
                            group_by=[],
                            return_records_with_no_metrics=True,
                            return_row_totals=False):
        """
        Retrieve a Campaign report from Apple and returns it as a Pandas DataFrame
        :param campaign: a Campaign object
        :param start_time: a string (yyyy-mm-dd), start time
        :param end_time:  a string (yyyy-mm-dd), end time
        :param timezone: UTC or ORTZ
        :param granularity: 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY'
        :param selector: an object with keys {conditions, fields, orderBy, pagination: # of results, default 20}
        :param group_by: field to group by
        :param return_row_totals: whether to return row totals or not
        :param return_records_with_no_metrics: whether to return zero rows or not
        :return: Pandas DataFrame containing the report
        """
        return _get_campaign_report(
            org_id=self.org_id,
            start_time=start_time,
            end_time=end_time,
            timezone=timezone,
            granularity=granularity,
            selector=selector,
            group_by=group_by,
            return_records_with_no_metrics=return_records_with_no_metrics,
            return_row_totals=return_row_totals
        )

    def create_campaign(self,
                        campaign_name,
                        ad_group_name,
                        app_id,
                        automatic_keywords_opt_in,
                        default_cpc_bid,
                        budget,
                        daily_budget,
                        cpa_goal=None,
                        payment_model="PAYG",
                        start_time=datetime.now(),
                        active=True):
        """
        Creates a new campaign and returns it
        :param campaign_name: name for the new campaign
        :param ad_group_name: name for the default ad group
        :param app_id: adamId of the app to be advertised
        :param automatic_keywords_opt_in: search match opt-in for the ad group
        :param default_cpc_bid: default cpc for the ad group
        :param budget: budget for the campaign
        :param daily_budget: daily budget for the campaign
        :param cpa_goal: CPA goal for the ad group
        :param payment_model: payment model for the campaign
        :param start_time: scheduled start time for the ad group
        :param active: whether the campaign is active of paused
        :return:
        """
        ad_group = AdGroup()
        ad_group.name = ad_group_name
        ad_group.automated_keywords_opt_in = automatic_keywords_opt_in
        if cpa_goal:
            ad_group.cpa_goal = {'amount': str(cpa_goal), 'currency': 'USD'}
        ad_group.default_cpc_bid = {'amount': str(default_cpc_bid),
                                    'currency': 'USD'}
        ad_group._start_time = "%4d-%02d-%02dT%02d:%02d:%02d.000" % (
            start_time.year,
            start_time.month,
            start_time.day,
            start_time.hour,
            start_time.minute,
            start_time.second
        )

        ad_group.keywords = []
        ad_group.status = "ENABLED" if active else "PAUSED"

        campaign = Campaign()
        campaign._adam_id = app_id
        campaign._org_id = self.org_id
        campaign.name = campaign_name
        campaign.budget_amount = {'amount': str(budget), 'currency': 'USD'}
        campaign.daily_budget_amount = {'amount': str(daily_budget),
                                        'currency': 'USD'}
        campaign._payment_model = payment_model

        campaign.status = "ENABLED" if active else "PAUSED"
        campaign.ad_groups = [ad_group]

        campaign.save(cascade=False)

        return self.get_campaign_by_name(campaign_name)
