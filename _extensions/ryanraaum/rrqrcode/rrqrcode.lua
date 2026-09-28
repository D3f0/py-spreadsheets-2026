
rrcounter = 0

local function make_table(nbits, pixel_size)
  local mt = {}
  for i=1,nbits*pixel_size do
    mt[i] = {}
    for j=1,nbits*pixel_size do
      mt[i][j] = 0
    end
  end
  mt.nbits = nbits
  mt.pixel_size = pixel_size
  return mt
end

local function color_pixel(mt, x, y, value)
  local imin = (x-1)*mt.pixel_size+1
  local imax = x*mt.pixel_size
  local jmin = (y-1)*mt.pixel_size+1
  local jmax = y*mt.pixel_size
  for i=imin,imax do
    for j=jmin,jmax do     
        mt[i][j] = value
    end
  end
end

local function scale(original, pixel_size, rounded)
  local newtable = make_table(#original, pixel_size)
  for i=1,#original do
    for j=1,#original do
      if original[i][j] > 0 then
        color_pixel(newtable, i, j, original[i][j])
      end
    end
  end
  return newtable
end

local function color_to_svg(color)
  return string.format("#%02x%02x%02x", color[1], color[2], color[3])
end

local function qrimg(str, options)
  local basename = quarto.base64.encode(str .. pandoc.utils.stringify(options))
  local img_name = basename..".svg"
  -- don't recreate qr codes if they already exist
  if pandoc.mediabag.lookup(img_name) then
    return true, img_name
  end
  local qrencode = require "qrencode"
  local res, qrtab = qrencode.qrcode(str)
  if not res then
    return false, nil
  end

  local modules = #qrtab
  local dark = color_to_svg(options.fgcolor)
  local svg = {
    string.format(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" shape-rendering="crispEdges">',
      modules, modules, options.size, options.size
    ),
  }
  if options.bgcolor[4] > 0 then
    svg[#svg + 1] = string.format(
      '<rect width="%d" height="%d" fill="%s" fill-opacity="%.3f"/>',
      modules, modules, color_to_svg(options.bgcolor), options.bgcolor[4] / 255
    )
  end
  for x=1,modules do
    for y=1,modules do
      if qrtab[x][y] > 0 then
        svg[#svg + 1] = string.format('<rect x="%d" y="%d" width="1" height="1" fill="%s"/>', y - 1, x - 1, dark)
      end
    end
  end
  svg[#svg + 1] = "</svg>"
  pandoc.mediabag.insert(img_name, "image/svg+xml", table.concat(svg))
  return true, img_name
end

local defaultOptions = {
  bgcolor = {255, 255, 255, 0}, -- fully transparent white
  fgcolor = {7, 54, 66, 255}, -- Solarized base02
  fpcolor = {7, 54, 66, 255}, -- Solarized base02
  size = 100,
  class = "qrcode",
}

local function isnil(obj) 
  -- pandoc over-rides nil elements with empty Inlines objects?
  return obj == nil or (type(obj) == "table" and #obj == 0)
end

local function onenumber(pandocList, alternative)
  if #pandocList == 1 then
    return tonumber(pandoc.utils.stringify(pandocList[1]))
  end
  return alternative
end

-- modified from https://gist.github.com/fernandohenriques/12661bf250c8c2d8047188222cab7e28
local function hex2rgb (hex)
    local hex = hex:gsub("#","")
    if hex:len() == 3 then
      return {(tonumber("0x"..hex:sub(1,1))*17), (tonumber("0x"..hex:sub(2,2))*17), (tonumber("0x"..hex:sub(3,3))*17)}
    else
      return {tonumber("0x"..hex:sub(1,2)), tonumber("0x"..hex:sub(3,4)), tonumber("0x"..hex:sub(5,6))}
    end
end

local function onecolor(pandocList, alternative)
  if #pandocList == 1 then
    local hex = pandoc.utils.stringify(pandocList[1])
    local rgb = hex2rgb(hex)
    if rgb[4] == nil then rgb[4] = 255 end
    return rgb
  end
  return alternative
end

local function onealpha(pandocList, alternative)
  if #pandocList == 1 then
    return math.floor(tonumber(pandoc.utils.stringify(pandocList[1])) * 255)
  end
  return alternative
end

local function oneclass(userstring, alternative)
  if #userstring > 1 then
    return userstring
  end
  return alternative
end

local function processNamedOptions(userOptions) 
  local mergedOptions = {}

  -- overall size and resolution
  mergedOptions.size = onenumber(userOptions.size, defaultOptions.size)
  mergedOptions.scale_multiplier = mergedOptions.size / 25
  
  -- main foreground color
  mergedOptions["fgcolor"] = onecolor(userOptions["fgcolor"], defaultOptions["fgcolor"])

  -- fpcolor follows main foreground color unless explicitly set
  mergedOptions["fpcolor"] = onecolor(userOptions["fpcolor"], mergedOptions["fgcolor"])

  -- update fg and fp color transparencies if necessary
  mergedOptions.fgcolor[4] = onealpha(userOptions.fgalpha, mergedOptions.fgcolor[4])
  mergedOptions.fpcolor[4] = onealpha(userOptions.fpalpha, mergedOptions.fpcolor[4])

  -- update background color if specified
  mergedOptions["bgcolor"] = onecolor(userOptions["bgcolor"], defaultOptions["bgcolor"])
  -- if we update the background color, make it opaque
  if not isnil(userOptions.bgcolor) then mergedOptions.bgcolor[4] = 255 end
  -- and if the user actively sets a background opacity, overwrite with that
  mergedOptions.bgcolor[4] = onealpha(userOptions.bgalpha, mergedOptions.bgcolor[4])

  mergedOptions.class = oneclass(pandoc.utils.stringify(userOptions.class), defaultOptions.class)

  return mergedOptions
end

return {
  ['rrqr'] = function(args, kwargs, _) 
    if args[1] == nil then
      quarto.log.error("rrqrcode: Some data are required for the QR Code")
      return pandoc.Null()
    end
    if args[2] ~= nil then
      id = pandoc.utils.stringify(args[2])
    else
      rrcounter = rrcounter + 1
      id = "rrqr" .. rrcounter
    end
    local updatedOptions = processNamedOptions(kwargs)
    local qrtext = pandoc.utils.stringify(args[1])
    local res, img_name = qrimg(qrtext, updatedOptions)
    if res then
      local attr = pandoc.Attr(id, {updatedOptions.class}, {{"width",updatedOptions.size}})
      return pandoc.Image({}, img_name, "", attr)  
    else
      quarto.log.error("rrqrcode: Could not create qrcode")
      return pandoc.Null()
    end
  end
}
