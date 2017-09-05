FORKED FROM https://github.com/BendingSpoons/searchads-api

# Apple Search Ads Python API
## Install instructions

1) Install the library with pip, running `pip install search_ads`
2) Go to: https://app.searchads.apple.com/cm/app/settings/apicertificates and download the certificates
3) Unzip the certificates
4) Create in the root of your Python project a text file called `.env` as follows:
```
SEARCH-ADS-PEM='<pem certificate full path>'
SEARCH-ADS-KEY='<key certificate full path>'
```
Alternatively you can set environment variables or use the `set_env` function as shown in the last example of this page.

## What can you do now?

* Edit Campaigns attributes
* Edit AdGroups attributes
* Edit Keywords attributes (*) 
* Add / Pause (*) keywords
* Work with reports (campaign, adgroup, keywords, search terms)
* Create a Campaign
* Create an Ad Group

(*) Note that editing keywords / removing keywords / removing campaigns operations are not allowed by the search ads v1 api. Where implemented they are implicitly translated as pausing the old keyword and creating a new one.

## Objects & methods quick ref:
* **SearchAds**
  * `get_campaigns`
  * `get_campaigns_by_name`
  * `get_campaign_keywords_report`
  * `get_campaign_searchterms_report`
  * `get_campaign_adgroups_report`
  * `get_campaign_report`
  * `create_campaign`
* **Campaign**
  * `pause`
  * `activate`
  * `get_ad_group_by_name`
  * `save`
* **AdGroup**
  * `pause`
  * `activate`
  * `save`
* **Keyword**
  * `pause`
  * `unpause`
  * `prepare_for_bulk_export`

Campaigns, AdGroups and Keywords have various properties that you can edit.
If you want to save all the changes done inside a campaign (including on its adgroups) simply call `save(cascade=True)` on it.

As always, when in doubt type `help()` or on any object you want to know more about

## Sample usage
```python
from search_ads import SearchAds

api = SearchAds("MyCompany")  # Our company account
campaign = api.get_campaigns_by_name('MyCampaing')[0]
ad_group = campaign.get_ad_group_by_name('Brand')

campaign.name = 'change my name!'
campaign.save()

ad_group.default_cpc_bid = '0.05'  # Amounts are strings

ad_group.keywords[0].text += "ss"
ad_group.keywords[0].bid_amount['amount'] = '0.6'
ad_group.save()  # Equivalently: campaign.save(cascade=True)
```

## Reports
```python
from search_ads import SearchAds

api = SearchAds("MyCompany")  # Our company account
campaign = api.get_campaigns_by_name('MyCampaign')[0]
print(api.get_campaign_adgroups_report(campaign))
```

Output:
```
     adGroupId        adGroupName  avgCPA  avgCPT  bidAmount  conversionRate  ...
0      123456  Generic Keywords     0.0     0.0       0.05             0.0
1      123456  Generic Keywords     0.0     0.0       0.05             0.0
2      123456  Generic Keywords     0.0     0.0       0.05             0.0
...
```

### Create a campaign, an ad group and add a keyword
```python
from search_ads import SearchAds
from search_ads import Campaign, Keyword, AdGroup

api = SearchAds("MyCompany")  # Our company account

campaign = api.create_campaign(
    campaign_name="fb test", # Campaign name
    ad_group_name="fb adGroup test", # AdGroup name
    app_id=284882215, # This should be a valid ID, this is facebook
    automatic_keywords_opt_in=False, # True if you want apple to choose keywords for you
    default_cpc_bid=1, # Default CPC bid in dollars (can be a float)
    budget=100, # Total budget for the campaign
    daily_budget=100 # Daily budget for the campaign
)

ad_group = campaign.ad_groups[0]
ad_group.keywords.append(
    Keyword(
        adGroupId = ad_group._id, # The id of the AdGroup
        text = "facebook", # The keyword text
        status = "ACTIVE", # Is the keyword active or paused?
        matchType = "EXACT", # Is the match broad or exact?
        bidAmount = {"amount":"1","currency":"USD"} # Bid amount object
    )
)
ad_group.save()
```

## Advanced Usage and Synchronization
This library also offers ways to programmatically set the certificates and to
batch-downloads reports (using time windows) to a local cache that can be later
used for further analysis


```python
from search_ads import SearchAds, DataBase
from search_ads import set_env
from search_ads import Keyword, Campaign, AdGroup, SyncManager

import pandas as pd
certs = {
    "SEARCH-ADS-PEM": "<path-to-your-pem>",
    "SEARCH-ADS-KEY": "<path-to-your-key>",
}

with set_env(**certs):
    api = SearchAds("MyCompany")
    campaigns=api.get_campaigns_by_name("MyApp")
    s = SyncManager(certs)
    for campaign in campaigns:
        campaign.set_sync_manager(s)
    print(campaigns)

    # Let's apply changes that won't be immediately written to the APIs
    for campaign in campaigns:
        campaign.name = 'pippo'  # Probably you don't want to do this..
        campaign.save()  # We are committing the changes to a local storage

    # Now it's time to write all our changes to our search ads account
    s.synchronize()

    # Let's now work with reports, downloading hourly data for all of our campaigns,
    # search terms, keywords and ad groups.
    db = DataBase()
    # This will take a while as it stores locally all the report data
    api.store_reports(campaigns, db)

# Let's find the daily average CPA per keyword over time
# Note that we have hourly data about this so we resample by day and average
df = db.reports[campaigns[0]]['keywords']
df.index = pd.to_datetime(df['date'])
df.groupby(['keyword', pd.TimeGrouper('D')])[['avgCPA']].mean()
```

And read/play with the DataFrame in output.

Enjoy!
