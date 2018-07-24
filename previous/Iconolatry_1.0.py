
#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

from struct import unpack_from, pack, calcsize
from PIL import Image, ImageCms
from tempfile import mkstemp
from math import isclose
from os.path import isfile, splitext
from io import BytesIO
import numpy

__name__        = "Iconolatry"
__version__     = "1.0"
__license__     = "MIT License"
__author__      = u"Matteo ℱan <SystemRage@protonmail.com>"
__copyright__   = "© Copyright 2018"
__url__         = "https://github.com/SystemRage/Iconolatry"
__summary__     = "Advanced Icon Converter"


## _______________
##| Read ICO/CUR  |-----------------------------------------------------------------------------------------------------------------------------------------
##|_______________|
##   
class READER( object ):

    def IsPng( self, data ):
        """ Determines whether a sequence of bytes is a PNG. """
        return data.startswith(b'\x89PNG\r\n\x1a\n')

    def GetImage( self, w, h, imdata ):
        """ Gets image from bytes. """
        global biBitCount

        if biBitCount == 32:
            ## 32-bit: BGRA.
            image = Image.frombytes('RGBA', (w, h), imdata, 'raw', 'BGRA', 0, -1)
        elif biBitCount == 24:
            ## 24-bit: BGR.
            image = Image.frombytes('RGB', (w, h), imdata, 'raw', 'BGR', 0, -1)
            ## Fix error screen (background isn't trasparent).
            ## Get max color (background).
            backg = max(image.getcolors(w * h))[1] 
            ## Put trasparency where's background.
            image = image.convert('RGBA')
            data = numpy.array(image)
            red, green, blue, alpha = data.T
            areas = (red == backg[0]) & (green == backg[1]) & (blue == backg[2])
            data[areas.T] = (backg[0], backg[1], backg[2], 0)
            image = Image.fromarray(data)
            
        return image
             
    def FromIcoCur( self, icocur, rebuild = False ):
        """ Reads an ICO/CUR file and checks whether it is acceptable. """

        valread = []
        log_err = ''

        if isinstance(icocur, str):
            if not isfile(icocur):
                log_err = 'Input: file "%s" not exists\n' %icocur
                return (valread, log_err)
            else:
                with open(icocur, 'rb') as file:
                    data = file.read()
        elif isinstance(icocur, bytes):
            data = icocur
        else:
            log_err = 'Input: neither a string file path nor bytes\n'
            return (valread, log_err)
  
        typ = {1:'ICO', 2:'CUR'}
        datasize = len(data)
        identf, count = unpack_from('<2H', data[2:6])
        
        ## Control if it's a ICO/CUR type and extract values.
        if identf not in [1, 2]:
            log_err = 'Get %s, Invalid ICO/CUR: Image type must be 1 or 2.\n' %identf
            return (valread, log_err)
        
        ## Note: always one frame for CUR.
        icondirentries = [ unpack_from('<4B2H2L', data[6 + 16*ii : 22 + 16*ii]) for ii in range(count) ]

        for ii in range(count):
            bWidth, bHeight, bColorCount, bReserved, hotx, hoty, dWBytesInRes, dWImageOffset = icondirentries[ii]
            bWidth = bWidth or 256
            bHeight = bHeight or 256

            if ii == 0:
                totalsize = dWImageOffset + dWBytesInRes
            else:
                totalsize += dWBytesInRes
                            
            icocurdata_with_header = data[dWImageOffset : dWImageOffset + dWBytesInRes]
            entry_is_png = self.IsPng( icocurdata_with_header )
            
            if not entry_is_png:
                if bWidth >= 256 or bHeight >= 256:
                    log_err = 'Entry #%d is a large image in uncompressed BMP format. It should be in PNG format.\n' %(ii+1)
                    return (valread, log_err)

                if rebuild:
                    new_icocurdata_with_header = MASK().RebuildANDMask( icocurdata_with_header, rebuild )
                    icocurdata = new_icocurdata_with_header[40 : dWBytesInRes]
                else:
                    if not MASK().RebuildANDMask( icocurdata_with_header, rebuild ):
                        log_err = 'Entry #%d has a bad mask that will display incorrectly in some places with Windows OS.\n' %(ii+1)
                        return (valread, log_err)
                    else:
                        icocurdata = icocurdata_with_header[40 : dWBytesInRes]

            ima = self.GetImage( bWidth, bHeight, icocurdata )
                                
            valread.append([ima, count, bWidth, bHeight, hotx, hoty])
        
        if datasize != totalsize:
            log_err = 'Invalid %s: Unexpected End Of File\n' %typ[identf] 
            return (valread, log_err)
        
        return (valread, log_err)


## __________________
##| Mask Operations  |--------------------------------------------------------------------------------------------------------------------------------------
##|__________________|
##        
class MASK( object ):
    
    def ComputeANDMask( self, imgdata, width, height ):
        """ Computes AND mask from 32-bit BGRA image data. """
        
        andbytes = []
        for y in range(height):
            bitcounter, currentbyte = (0 for _ in range(2))
            for x in range(width):
                alpha = imgdata[(y * width + x) * 4 + 3]
                currentbyte <<= 1
                if alpha == 0:
                    currentbyte |= 1
                bitcounter += 1
                if bitcounter == 8:
                    andbytes.append(currentbyte)
                    bitcounter, currentbyte = (0 for _ in range(2))
            ## Pad current byte at the end of row.
            if bitcounter > 0:
                currentbyte <<= (8 - bitcounter)
                andbytes.append(currentbyte)
            ## Keep padding until multiple 4 bytes.
            while len(andbytes) % 4 != 0:
                andbytes.append(0)
                
        andbytes = b"".join(pack('B', andbyte) for andbyte in andbytes)
        return andbytes
    

    def CheckANDMask( self, xordata, anddata, width, height ):
        """ Verifies if AND mask is good for 32-bit BGRA image data.
            1- Checks if AND mask is opaque wherever alpha channel is not fully transparent.
            2- Checks inverse rule, AND mask is transparent wherever alpha channel is fully transparent. """
        
        xorbytes = width * 4
        andbytes = WRITER().CalcRowSize( 1, width )
        for y in range(height):
            for x in range(width):
                alpha = ord(bytes([xordata[y * xorbytes + x * 4 + 3]]))
                mask = bool(ord(bytes([anddata[y * andbytes + x // 8]])) & (1 << (7 - (x % 8))))
                if mask:
                    if alpha > 0:
                        ## mask transparent, alpha partially or fully opaque. This pixel
                        ## can show up as black on Windows due to a rendering bug.
                        return False
                else:
                    if alpha == 0:
                        ## mask opaque, alpha transparent. This pixel should be marked as
                        ## transparent in the mask, for legacy reasons.
                        return False
        return True


    def RebuildANDMask( self, data, rebuild = False ):
        """ Checks AND mask in an icon image for correctness, or rebuilds it.
            With rebuild == False, checks whether the mask is bad.
            With rebuild == True, throw the mask away and recompute it from the alpha channel data. """
        global biBitCount
        
        ## Get BITMAPINFO header data.
        (biSize, biWidth, biHeight, biPlanes, biBitCount,
        biCompression, biSizeImage, biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant) = unpack_from('<3L2H6L', data[0:40])

        if biBitCount != 32:
            ## No alpha channel, so the mask cannot be wrong.
            return (data if rebuild else True)
        
        biHeight = int(biHeight / 2.)
        xorsize = WRITER().CalcRowSize( biBitCount, biWidth ) * biHeight
        ## Checks if is used a palette.
        xorpalettesize = (biClrUsed or (1 << biBitCount if biBitCount < 24 else 0)) * 4
        xordata = data[40 + xorpalettesize : 40 + xorpalettesize + xorsize]

        if rebuild:
            anddata = self.ComputeANDMask( xordata, biWidth, biHeight )
            ## Replace the AND mask.
            fixed = data[0 : 40 + xorpalettesize + xorsize] + anddata
            return fixed
        else:
            anddata = data[40 + xorpalettesize + xorsize : len(data)]
            return self.CheckANDMask( xordata, anddata, biWidth, biHeight )
        

## ____________
##| Write ICO  |--------------------------------------------------------------------------------------------------------------------------------------------
##|____________|
##
class WRITER( object ):
    
    def GetParameters( self, paths ):
        """ Prints parameters for test images. """
        for path in paths:
            with open(path, 'rb') as file:
                    data = file.read(30)
            bpc, colortype = unpack_from('<2B', data[24:26])
            print('Image %s have bit per channel = %s and colortype = %s' %(path, bpc, colortype))
            
            img = Image.open(path)
            p = img.getpixel((0,0)) ## hack: this correct the palette mode.
            print('Mode image is %s' %img.mode)
            if 'transparency' in img.info:
                    print('Image with transparency')
            else:
                    print('No transparency')
            try:
                    print('Mode palette is %s' %img.palette.mode)
            except:
                    print('No palette')

    def CalcRowSize( self, bits, image_width ):
        """ Computes the number of bytes per row in a image. """
        ## The size of each row is rounded up to the nearest multiple of 4 bytes.
        rowsize = int(((bits * image_width + 31) // 32)) * 4
        return rowsize

    def HeaderIcondir( self, idCount ):
        """ Defines the ICONDIR header. """
        ## (2bytes)idReserved (always 0) - (2bytes)idType (ico=1, cur=2) - (2bytes)idCount.
        idReserved = 0
        idType = 1
        head = pack('3H', idReserved, idType, idCount)
        return head

    def HeaderBmpinfo( self, bWidth, bHeight, wBitCount, imgdata, bColorCount ):
        """ Defines the BMPINFO header. """
        ## (4bytes)biSize - (4bytes)biWidth - (4bytes)biHeight - (2bytes)biPlanes - (2bytes)biBitCount -
        ## - (4bytes)biCompression - (4bytes)biSizeImage -
        ## - (4bytes)biXPelsPerMeter - (4bytes)biYPelsPerMeter - (4bytes)biClrused - (4bytes)biClrImportant.
        biSize = calcsize('3I2H2I2i2I')
        biWidth = bWidth
        biHeight = bHeight * 2  # include the mask height
        biPlanes = 1            # color planes must be 1 
        biBitCount = wBitCount  # 1, 2, 4, 8, 16, 24, 32 
        biCompression = 0       # only uncompressed images BI_RGB.
        biSizeImage = len(imgdata) + self.CalcRowSize( 1, bWidth ) * abs(bHeight)  # calculate pixel array size
        biXPelsPerMeter = 0
        biYPelsPerMeter = 0
        biClrUsed = bColorCount
        biClrImportant = 0
        
        bmpinfoheader = pack('3I2H2I2i2I', biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage,
                             biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant)
        return bmpinfoheader

                        
    def LoadImage( self, image_path, N ):
        """ Loads image types. """
        global flag_bit, log_mess

        ## Open PIL image.
        try:
            img = Image.open(image_path, mode = 'r')
        except:
            name, extension = splitext(image_path)
            log_err = ' Format "%s" is not readable from PIL\n'%extension
            return log_err
        
        mode = img.mode
        frmt = img.format
        log_mess = '%s with mode "%s"' %(image_path, mode)
        ## Convert to PNG in memory.
        imgbyteio = BytesIO()
        img.save(imgbyteio, format = 'PNG')
        dataim = imgbyteio.getvalue()

        if frmt != 'PNG':
            img = Image.open(imgbyteio)
            
        ## Get bit depth from image PNG.
        ## PNG bits per sample or per palette index (not per pixel)
        ## PNG color type represent sums of this values: 1 (palette used), 2 (color used) and 4 (alpha channel used)

        ## Color Option     -   Channels  -  Bits per channel - Bits per pixel - Color type - Interpretation
        ##  indexed                 1           1,2,4,8             1,2,4,8           3        each pixel is a palette index 
        ##  grayscale               1           1,2,4,8,16          1,2,4,8,16        0        each pixel is a grayscale sample
        ##  grayscale+alpha         2           8,16                16,32             4        each pixel is a grayscale sample followed by an alpha sample
        ##  truecolor               3           8,16                24,48             2        each pixel is an R,G,B triple
        ##  truecolor+alpha         4           8,16                32,64             6        each pixel is an R,G,B triple followed by an alpha sample
                         
        bitdepth, colortype = unpack_from('<2B', dataim[24:26])
        bpp = len(img.getbands()) * bitdepth

        ## Write bpp in log.
        log_mess += ' have bpp = %s bit' %bpp
        
              
        def FlyConversion( image, newmode, oldmode, oldbpp, logm, flag_t, flag_b ):
            if flag_t or flag_b or oldmode in ['P','PA','LA', 'L', 'I', '1'] :
                image = image.convert(newmode)

                dictbit = {'RGB':24,
                           'RGBA':32,
                           'P':8,
                           'L':8,
                           'I':16
                           }
                newbpp = dictbit[newmode]
                
                if flag_t:
                    logm += ', after transparency conversion to mode "%s" have now bpp = %s bit' %(newmode, newbpp)
                elif flag_b:
                    logm += ', user converted to mode "%s" have now bpp = %s bit ' %(newmode, newbpp)
                else:
                    logm += ', after automatic conversion to mode "%s" have now bpp = %s bit' %(newmode, newbpp)
            else:
                newbpp = oldbpp
            return image, newmode, newbpp, logm
        
        
        def GetBGRA( image ):
            try:
                imagedata = image.tobytes('raw', 'BGRA', 0, -1)
            except SystemError:
                ## Workaround for earlier versions.
                r, g, b, a = image.split()
                image = Image.merge('RGBA', (b, g, r, a))
                imagedata = image.tobytes('raw', 'BGRA', 0, -1)
            return imagedata
        

        def FlyResize( image, log_mess, nimages, method = Image.ANTIALIAS ):
            """ Changes size of images,
                to correct conversion problems of sizes too large. """
            oldw, oldh = image.size
            resl = [8, 10, 14, 16, 20, 22, 24, 32, 40, 48, 64, 96, 128, 256]
           
            if oldw > 256 or oldh > 256:
                newsiz = min(resl, key = lambda x:abs(x - max(oldw, oldh)))
                image.thumbnail((newsiz, newsiz), method)
                neww, newh = image.size
                log_mess += ' and new size scaled = %s x %s' %(neww, newh)
            elif nimages > 1:
                log_mess += ' and size = %s x %s' %(oldw, oldh)
                
            return oldw, oldh, image, log_mess
        

        ##                fixbit=True    fixbit=False
        ##--------------------------------------------------
        ##  "RGB;24,48"     RGB;24        RGB;24, *RGB;48
        ##  "RGB+transp"    RGBA;32       RGBA;32
        ##  "RGBA;32,64"    RGBA;32       RGBA;32, *RGBA;64
        ##--------------------------------------------------
        ##  "P;8"           RGBA;32       P;8
        ##  "P;1,2,4"       RGBA;32       RGBA;32
        ##  "P+transp"      RGBA;32       RGBA;32
        ##  "PA"            RGBA;32       RGBA;32
        ##--------------------------------------------------
        ##  "LA;16,32"      RGBA;32       RGBA;32
        ##  "L;2,4,8"       RGBA;32       RGBA;32
        ##  "L+transp"      RGBA;32       RGBA;32
        ##  "I;16"          RGBA;32       RGBA;32
        ##  "1"             RGBA;32       RGBA;32
        ##--------------------------------------------------
        ## Note: *convertible but visualization not supported.

        ## TODO: if possible with (fixbit=False) "L;2,4,8" --> L;2,4,8 
        ##           conversion                  "I;16"    --> I;16
        ##                                       "1"       --> 1
        ##                                       "P;1,2,4" --> P;1,2,4

        ## Resize.
        oldw, oldh, img, log_mess = FlyResize( img, log_mess, N, method = Image.ANTIALIAS )
        
        ## Manage ICC.
        if 'icc_profile' in img.info:
            icc = mkstemp(suffix = '.icc')[1]
            with open(icc, 'wb') as iccfil:
                iccfil.write(img.info.get('icc_profile'))
            srgb = ImageCms.createProfile('sRGB')
            img = ImageCms.profileToProfile(img, icc, srgb)
            
        ## Manage Trasparency.
        flag_trans = False
        if 'transparency' in img.info:
            flag_trans = True            
            img, mode, bpp, log_mess = FlyConversion( img, 'RGBA', mode, bpp, log_mess, flag_trans, flag_bit )
            imgdata = GetBGRA( img )
            
        ## Read data bytes.   
        if not flag_trans:
            if mode == 'RGB':
                img, mode, bpp, log_mess = FlyConversion( img, 'RGB', mode, bpp, log_mess, flag_trans, flag_bit )
                imgdata = img.tobytes('raw', 'BGR', 0, -1)  #unpadded, reversed.
                         
            elif mode == 'P':
                if flag_bit or bpp != 8:
                    img, mode, bpp, log_mess = FlyConversion( img, 'RGBA', mode, bpp, log_mess, flag_trans, flag_bit )
                    imgdata = img.tobytes('raw', 'BGRA', 0, -1)
                else:
                    imgdata = img.tobytes('raw', 'P', 0, -1)
                    
            elif mode in ['1', 'I', 'L', 'LA', 'PA', 'RGBA']:
                if mode == 'I':
                    ## To prevent PIL problems, convert I 16 bit to grayscale 8 bit; then to RGBA.
                    table = [ i/(2**(bitdepth/2)) for i in range(2**bitdepth) ]
                    img = img.point(table, 'L')
                
                img, mode, bpp, log_mess = FlyConversion( img, 'RGBA', mode, bpp, log_mess, flag_trans, flag_bit )
                imgdata = GetBGRA( img )
                                            
        return img, imgdata, mode, bpp
    

    def Build( self, image_paths, output_path ):
        """ Creates and saves the ICO file. """
        global log_mess
        
        ico_data, partial_log = [ '' for _ in range(2) ]
        img_data = b''
        ## Define header of ICO file.
        num_images = len(image_paths)
        ico_data = self.HeaderIcondir( num_images )

        ## Size of all the headers (image headers + file header)
        ## (1byte)bWidth - (1byte)bHeight - (1byte)bColorCount - (1byte)bReserved -
        ## -(2bytes)wPlanes - (2bytes)wBitCount - (4bytes)dwBytesInRes - (4bytes)dwImageOffset.
        dataoffset = calcsize('4B2H2I') * num_images + calcsize('HHH')

        ## Create ICO.
        for ii, image in enumerate(image_paths):
            values_or_err = self.IcondirEntry( image, dataoffset, num_images )
            try:
                icondirentry, imgdata, dataoffset = values_or_err
                ico_data += icondirentry
                img_data += imgdata
                partial_log += (log_mess + '; ' if num_images - ii > 1 else log_mess)
            except ValueError:
                return values_or_err
                
        ## Save ICO.
        with open(output_path, 'wb') as f_ico:  
            f_ico.write(ico_data)
            f_ico.write(img_data)

        log_mess = partial_log
        log_mess += ' --> Successfully wrote icon to %s.' %output_path
        return log_mess
            
            
    def IcondirEntry( self, image_path, dataoffset, N ):
        """ Defines data for ICO file creation. """
            
        img, imgdata, mode, bpp = self.LoadImage( image_path, N )
        
        bWidth, bHeight = img.size
        bReserved = 0
        wPlanes = 0      
        wBitCount = bpp
        
        if wBitCount <= 8 and mode == 'P':
            try:
                palettemode, palettedata = img.palette.getdata()
                lenpal = len(palettedata)
                bColorCount = lenpal // 3
            except:
                log_err = 'Image Malformed --> No correct palette for image %s\n' %image_path
                return log_err
        else:
            bColorCount = 0
        
        dwImageOffset = dataoffset

        ## Generate BITMAPINFO header.
        data = self.HeaderBmpinfo( bWidth, bHeight, wBitCount, imgdata, bColorCount )
        
        ## Write the palette.
        if mode == 'P':
            if palettemode in ['RGB;L', 'RGB']:
                for x in range(0, lenpal, 3):
                    ## B, G, R, 0.
                    data += bytes([palettedata[x + 2]]) + bytes([palettedata[x + 1]]) + bytes([palettedata[x]])
                    data += pack('B', 0)
                    
            elif palettemode in ['RGBA;L', 'RGBA']:
                for x in range(0, lenpal, 4):
                    ## B, G, R, A.
                    data += bytes([palettedata[x + 2]]) + bytes([palettedata[x + 1]]) + bytes([palettedata[x]]) + bytes([palettedata[x + 3]])
       
        ## Write XOR mask (Image).
        data += imgdata
        
        ## Write AND mask (Transparency).
        rowsize = self.CalcRowSize( 1, bWidth )
        masksize = rowsize * abs(bHeight)

        if mode == 'RGBA':
             data += MASK().ComputeANDMask( imgdata, bWidth, bHeight )
        elif mode in ['RGB', 'P']:
            data += pack('B', 0) * masksize
       
        ## Increment data offset.
        dataoffset += len(data)

        ## Calculate size of icondirentry + image data.
        dwBytesInRes = len(data)

        ## Define correct dimension, 0 means 256 (or more).
        if bWidth  >= 256: bWidth = 0
        if bHeight >= 256: bHeight = 0
        
        # Pack the icondirentry header.
        icondirentry = pack('4B2H2I', bWidth, bHeight, bColorCount, bReserved, wPlanes, wBitCount, dwBytesInRes, dwImageOffset)

        return icondirentry, data, dataoffset


    def ToIco( self, forced_bpp_conversion, imagepaths, icopaths ):
        """ Process images to create ICO."""
        global flag_bit
        
        flag_bit = forced_bpp_conversion
        all_log_mess = []
        
        ## Checks icopaths.
        if not icopaths:
            log_err = 'Output: file/s missing\n'
            return log_err
        else:
            if isinstance(icopaths, list):
                for path in icopaths:
                    if not path.lower().endswith('.ico'):
                        log_err = 'Output: file "%s" with wrong file extension' %path
                        return log_err
            else:
                log_err = 'Output: file/s not in a list\n'
                return log_err
                    
        ## Checks imagepaths.
        if not imagepaths:
            log_err = 'Input: file/s missing\n'
            return log_err
        for ii, paths in enumerate(imagepaths):
            if isinstance(paths, list):
                if not paths:
                    log_err = 'Input: file/s missing\n'
                    return log_err
                else:
                    for path in paths:
                        if not isfile(path):
                            log_err = 'Input: file "%s" not exists\n' %path
                            return log_err
            else:
                log_err = 'Input: entry #%s is not a list\n' %ii
                return log_err
            
        ## Do process.
        for path in zip(imagepaths, icopaths):
            all_log_mess.append(self.Build( path[0], path[1] ))
            
        return all_log_mess
    
##----------------------------------------------------------------------------------------------------------------------------------------------------------
