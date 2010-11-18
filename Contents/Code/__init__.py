# AdultDVDEmpire

# URLS
ADE_BASEURL = 'http://www.adultdvdempire.com/'
ADE_SEARCH_MOVIES = ADE_BASEURL + 'SearchTitlesPage.aspx?SearchString=%s'
ADE_MOVIE_INFO = ADE_BASEURL + '%s/'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')

class ADEAgent(Agent.Movies):
  name = 'Adult DVD Empire'
  languages = [Locale.Language.English]
  primary_provider = True

  def search(self, results, media, lang):
    title = media.name
    if media.primary_metadata is not None:
      title = media.primary_metadata.title

    if title.startswith('The '):
      if title.count(':'):
        title = title.split(':',1)[0].replace('The ','',1) + ', The:' + title.split(':',1)[1]
      else:
        title = title.replace('The ','',1) + ', The'

    query = String.URLEncode(String.StripDiacritics(title.replace('-','')))
    for movie in HTML.ElementFromURL(ADE_SEARCH_MOVIES % query).xpath('//div[contains(@class,"ListItem_ItemTitle")]/a'):
      curName = movie.text_content().strip()
      curID = movie.get('href').split('/',2)[1]
      score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower())
      if score >= 85:
        if curName.count(', The'):
          curName = 'The ' + curName.replace(', The','',1)
        results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))

    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    html = HTML.ElementFromURL(ADE_MOVIE_INFO % metadata.id)
    metadata.title = media.title

    # Get Thumb and Poster
    try:
      img = html.xpath('//div[@id="ctl00_ContentPlaceHolder_ctl00_pnl_Default"]/a/img[contains(@src,"m.jpg")]')[0]
      thumbUrl = img.get('src')
      thumb = HTTP.Request(thumbUrl)
      posterUrl = img.get('src').replace('m.jpg','h.jpg')
      metadata.posters[posterUrl] = Proxy.Preview(thumb)
    except:
      pass

    # Get tagline
    try: metadata.tagline = html.xpath('//span[@class="Item_InfoTagLine"]')[0].text_content().strip()
    except: pass

    # Summary.
    try:
      metadata.summary = html.xpath('//div[@class="Item_InfoContainer"]')[0].text_content().replace('\t','').strip()
      if metadata.summary.find(metadata.tagline) != -1:
        metadata.summary = metadata.summary.replace(metadata.tagline, '').strip()
    except: pass

    # Other data.
    data = {}
    for div in html.xpath('//div[@class="Item_ProductInfoSectionConatiner"]/div'):
      name, value = div.text_content().split(':')
      data[name.strip()] = value.strip()

    if data.has_key('Rating'):
      metadata.content_rating = data['Rating']

    if data.has_key('Studio'):
      metadata.studio = data['Studio']

    if data.has_key('Release Date'):
      try:
        metadata.originally_available_at = Datetime.ParseDate(data['Release Date']).date()
        metadata.year = metadata.originally_available_at.year
      except: pass

