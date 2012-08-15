# AdultDVDEmpire

# URLS
ADE_BASEURL = 'http://www.adultdvdempire.com'
ADE_SEARCH_MOVIES = ADE_BASEURL + '/dvd/search?q=%s'
ADE_MOVIE_INFO = ADE_BASEURL + '/%s/'

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


    query = String.URLEncode(String.StripDiacritics(title.replace('-','')))
    # Finds div with class=item
    for movie in HTML.ElementFromURL(ADE_SEARCH_MOVIES % query).xpath('//p[contains(@class,"title")]/a'):
      # curName = The text in the 'title' p
      curName = movie.text_content().strip()
      if curName.count(', The'):
        curName = 'The ' + curName.replace(', The','',1)

      # curID = the ID portion of the href in 'movie'
      curID = movie.get('href').split('/',2)[1]
      score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower())
      if curName.lower().count(title.lower()):
        results.Append(MetadataSearchResult(id = curID, name = curName, score = 100, lang = lang))
      elif (score >= 95):
        results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))

    results.Sort('score', descending=True)

  def update(self, metadata, media, lang):
    html = HTML.ElementFromURL(ADE_MOVIE_INFO % metadata.id)
    metadata.title = media.title

    # Get Thumb and Poster
    try:
      img = html.xpath('//div[@id="Boxcover"]/a/img[contains(@src,"m.jpg")]')[0]
      thumbUrl = img.get('src')
      thumb = HTTP.Request(thumbUrl)
      posterUrl = img.get('src').replace('m.jpg','h.jpg')
      metadata.posters[posterUrl] = Proxy.Preview(thumb)
    except:
      pass

    # Get tagline
    try: metadata.tagline = html.xpath('//p[@class="Tagline"]')[0].text_content().strip()
    except: pass

    # Summary.
    try:
      metadata.summary = html.xpath('//div[@class="Section Synopsis"]')[0].text_content().replace('\t','').strip()
      if metadata.summary.find("Synopsis") != -1:
        metadata.summary = metadata.summary.replace("Synopsis", '').strip()
      if metadata.summary.find(metadata.tagline) != -1:
        metadata.summary = metadata.summary.replace(metadata.tagline, '').strip()
    except: pass

    # Other data.

    data = {}
    productinfo = HTML.StringFromElement(html.xpath('//div[@class="Section ProductInfo"]')[0])
    productinfo = productinfo.replace('<strong>', '|')
    productinfo = productinfo.replace('</strong>', ':').split('<h2>Detail</h2>')
    productinfo = HTML.ElementFromString(productinfo[1]).text_content()

    for div in productinfo.split('|'):
      if ':' in div:
        name, value = div.split(':')
        data[name.strip()] = value.strip()

    if data.has_key('Rating'):
      metadata.content_rating = data['Rating']
      #Log.Debug(data['Rating'])

    if data.has_key('Studio'):
      metadata.studio = data['Studio']
      #Log.Debug(data['Studio'])

    if data.has_key('Released'):
      #Log.Debug(data['Released'])
      try:
        metadata.originally_available_at = Datetime.ParseDate(data['Released']).date()
        metadata.year = metadata.originally_available_at.year
      except: pass

    #Get Cast
    try:
      metadata.roles.clear()
      htmlcast = html.xpath('//div[@class="Section Cast"]/ul/li/a[@class="PerformerName"]')
      for cast in htmlcast:
        cname = cast.text_content().strip()
        if ((cname != "(bio)") and (cname != "(interview)") and (len(cname) > 0)):
          #Log(cname)
          cpage = HTML.ElementFromURL(ADE_BASEURL + cast.get('href')).xpath('//div[@id="Headshot"]/img')[0]
          cimg = cpage.get('src')
          #Log(cimg)
          role = metadata.roles.new()
          role.actor = cname
          role.photo = cimg
    except: pass