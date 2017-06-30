import json

from search_ads.api.utils import api_put, api_post, set_env
from search_ads.models.utils import Synchronizable, AppleSerializable, Serializable


class SyncManager(Serializable):
    """
    Synchronize Manager Object
    """

    def __init__(self, certs):
        self.certs = certs
        self.pending_actions = []

    def synchronize(self):
        with set_env(**self.certs):
            for i, (obj, json_data, args, kwargs) in enumerate(self.pending_actions):
                kwargs['force_sync'] = True
                # :TODO: actions could be executed in parallel
                print(obj)
                if obj == 'Campaign':
                    obj = Campaign(**json.loads(json_data))
                else:
                    obj = AdGroup(**json.loads(json_data))
                obj.save(*args, **kwargs)
                del self.pending_actions[i]


class AdGroup(Synchronizable, AppleSerializable):
    def __init__(self,
                 cpaGoal=None,
                 startTime=None,
                 storefronts=["US"],
                 name=None,
                 displayStatus=None,
                 targetingDimensions=None,
                 defaultCpcBid=None,
                 status=None,
                 automatedKeywordsOptIn=None,
                 servingStatus=None,
                 servingStateReasons=None,
                 id=None,
                 negativeKeywords=[],
                 campaignId=None,
                 keywords=[],
                 modificationTime=None,
                 endTime=None,
                 **kwargs):
        """
        Creates an Ad Group object
        :param cpaGoal:
        :param startTime:
        :param storefronts:
        :param name:
        :param displayStatus:
        :param targetingDimensions:
        :param defaultCpcBid:
        :param status:
        :param automatedKeywordsOptIn:
        :param servingStatus:
        :param servingStateReasons:
        :param id:
        :param negativeKeywords:
        :param campaignId:
        :param keywords:
        :param modificationTime:
        :param endTime:
        :param kwargs:
        """
        self._start_time = startTime
        self._storefronts = storefronts
        self.name = name
        self.targeting_dimensions = targetingDimensions
        self.status = status
        self._serving_status = servingStatus
        self._serving_state_reasons = servingStateReasons
        self.automated_keywords_opt_in = automatedKeywordsOptIn
        self._campaign_id = str(campaignId)
        self.cpa_goal = cpaGoal
        self.default_cpc_bid = defaultCpcBid
        self._display_status = displayStatus
        self._end_time = endTime
        self._id = str(id)
        self.keywords = []
        self._negative_keywords = []
        self._modification_time = modificationTime

        self.sync_manager = None

        for keyword in negativeKeywords:
            self._negative_keywords.append(Keyword(**keyword))

        for keyword in keywords:
            self.keywords.append(Keyword(**keyword))

    def __repr__(self):
        return "{name} (Ad Group id: {id})".format(name=self.name, id=self._id)

    def __editable_fields(self):
        as_json = {
            "name": self.name,
            "defaultCpcBid": self.default_cpc_bid,
            "cpaGoal": self.cpa_goal,
            "automatedKeywordsOptIn": self.automated_keywords_opt_in,
            "targetingDimensions": self.targeting_dimensions,
            "status": self.status,
        }
        if not self._id:
            as_json["startTime"] = self._start_time
        return as_json

    def pause(self):
        """
        Pause the Ad Group
        """
        self.status = "PAUSED"

    def activate(self):
        """
        Activate the Ad Group (unpause)
        """
        self.status = "ENABLED"

    def save(self, verbose=False, force_sync=False,
             save_callback=lambda x: x):
        """
        Save the AdGroup object
        :param force_sync: Force Sync to Apple APIs
        :param save_callback: Callback function called with the json
                                 serialized object as arg
        :param verbose: Verbosity
        """
        if force_sync or super().synchronize(self,
                                             save_callback=save_callback):
            keywords_export = []
            for keyword in self.keywords:
                keywords_export.extend(
                    keyword.prepare_for_bulk_export(self._campaign_id,
                                                    self._id))
            api_post("keywords/targeting/", data=keywords_export,
                     verbose=verbose)
            if self._id:
                api_put(
                    "campaigns/%s/adgroups/%s" % (self._campaign_id, self._id),
                    data=self.__editable_fields(), verbose=verbose)
            else:
                api_post("campaigns/%s/adgroups" % (self._campaign_id),
                         data=self.__editable_fields(),
                         verbose=verbose)


class Campaign(Synchronizable, AppleSerializable):
    def __init__(self,
                 id=None,
                 orgId=None,
                 name=None,
                 budgetAmount=None,
                 adamId=None,
                 paymentModel=None,
                 locInvoiceDetails=None,
                 budgetOrders=None,
                 dailyBudgetAmount=None,
                 status=None,
                 servingStatus=None,
                 displayStatus=None,
                 servingStateReasons=None,
                 negativeKeywords=[],
                 storefront=[],
                 adGroups=[],
                 modificationTime=None,
                 **kwargs):
        """
        Creates a Campaign object
        :param id:
        :param orgId:
        :param name:
        :param budgetAmount:
        :param adamId:
        :param paymentModel:
        :param locInvoiceDetails:
        :param budgetOrders:
        :param dailyBudgetAmount:
        :param status:
        :param servingStatus:
        :param displayStatus:
        :param servingStateReasons:
        :param negativeKeywords:
        :param adGroups:
        :param modificationTime:
        :param kwargs:
        """
        self._id = str(id)
        self._org_id = str(orgId)
        self._adam_id = str(adamId)
        self._payment_model = paymentModel
        self._serving_status = servingStatus
        self._display_status = displayStatus
        self._serving_state_reasons = servingStateReasons
        self._modification_time = modificationTime
        self._storefront = storefront

        self.name = name
        self.budget_amount = budgetAmount
        self.daily_budget_amount = dailyBudgetAmount
        self.loc_invoice_details = locInvoiceDetails
        self.budget_orders = budgetOrders
        self.status = status

        self._negative_keywords = []
        for keyword in negativeKeywords:
            self._negative_keywords.append(Keyword(**keyword))

        self.ad_groups = []
        for ad_group in adGroups:
            self.ad_groups.append(AdGroup(**ad_group))

        self.sync_manager = None

    def __repr__(self):
        return "{name} (Campaign id: {id})".format(name=self.name, id=self._id)

    def pause(self):
        """
        Pause the campaign
        """
        self.status = "PAUSED"

    def activate(self):
        """
        Activate the campaign (unpause)
        """
        self.status = "ENABLED"

    def get_ad_group_by_name(self, name):
        """
        Get Ad Group matching the input name
        :param name: name of the Ad Group to match
        :return: AdGroup matching object
        """
        for ad_group in self.ad_groups:
            if ad_group.name == name:
                return ad_group

    def __editable_fields(self):
        as_json = {
            "name": self.name,
            "budgetAmount": self.budget_amount,
            "locInvoiceDetails": self.loc_invoice_details,
            "budgetOrders": self.budget_orders,
            "dailyBudgetAmount": self.daily_budget_amount,
            "status": self.status,
        }
        if not self._id:
            as_json['adGroups'] = [i.__editable_fields() for i in
                                   self.ad_groups]
        return as_json

    def save(self, cascade=True, verbose=False, force_sync=False,
             save_callback=lambda x: x):
        """
        Save the Campaign
        :param cascade: Also save recursively all attached AdGroups
        :param force_sync: Force Sync to Apple APIs
        :param save_callback: Callback function called with the json
                                 serialized object as arg
        :param verbose: Verbosity
        """
        if force_sync or super().synchronize(self,
                                             save_callback=save_callback):
            if cascade:
                for ad_group in self.ad_groups:
                    ad_group.save(verbose=verbose)
            if self._id:
                api_put("campaigns/%s" % self._id,
                        data=self.__editable_fields(),
                        org_id=self._org_id,
                        verbose=verbose)
            else:
                api_post("campaigns/", data=self.__editable_fields(),
                         org_id=self._org_id, verbose=verbose)


class Keyword(object):
    def __init__(self,
                 adGroupId,
                 matchType,
                 status,
                 text,
                 bidAmount=None,
                 modificationTime=None,
                 id=None,
                 **kwargs):
        """
        Keyword Object
        :param adGroupId:
        :param matchType:
        :param status:
        :param text:
        :param bidAmount:
        :param modificationTime:
        :param id:
        :param kwargs:
        """
        self._ad_group_id = str(adGroupId)
        self.bid_amount = bidAmount
        self._id = str(id)
        self.match_type = matchType
        self._modification_time = modificationTime
        self.status = status
        self.__text = text
        self.__updated_text = None

    def __repr__(self):
        return "{text} (Keyword id: {id})".format(text=self.text, id=self._id)

    def __editable_fields(self):
        as_dict = {
            'adGroupId': str(self._ad_group_id),
            'bidAmount': self.bid_amount,
            'matchType': self.match_type,
            'status': self.status,
            'text': self.text,
        }
        return as_dict

    @property
    def text(self):
        return self.__updated_text if self.__updated_text else self.__text

    @text.setter
    def text(self, value):
        self.__updated_text = value

    def pause(self):
        """
        Pause the keyword
        """
        self.status = "PAUSED"

    def activate(self):
        """
        Activate the keyword (unpause)
        """
        self.status = "ENABLED"

    def prepare_for_bulk_export(self, campaign_id, ad_group_id):
        """
        Prepare Keyword for bulk export
        :param campaign_id: the id of the Campaign
        :param ad_group_id: the id of the Ad Group
        :return: a list of keywords for bulk export
        """
        if not self.__updated_text or (self.__updated_text and not self._id):
            return [{
                'importAction': 'UPDATE' if self._id else 'CREATE',
                'campaignId': str(campaign_id),
                'adGroupId': str(ad_group_id),
                'bidAmount': self.bid_amount,
                'id': str(self._id),
                'matchType': self.match_type,
                'status': self.status,
                'text': self.text,
            }]
        else:
            return [{
                'importAction': 'UPDATE',
                'campaignId': str(campaign_id),
                'adGroupId': str(ad_group_id),
                'bidAmount': self.bid_amount,
                'id': str(self._id),
                'matchType': self.match_type,
                'status': 'PAUSED',  # Pause the old keyword anyway
                'text': self.__text,
            }, {
                'importAction': 'CREATE',
                'campaignId': str(campaign_id),
                'adGroupId': str(ad_group_id),
                'bidAmount': self.bid_amount,
                'id': str(self._id),
                'matchType': self.match_type,
                'status': self.status,
                'text': self.__updated_text,
            }]
