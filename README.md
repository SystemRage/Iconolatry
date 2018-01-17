# Iconolatry
> *Advanced Icon Converter*

## Why
There are several online converters, icon makers and favicon generators that can 
transform many image formats in *.ICO* files or to achieve reverse process,
but only a few of them are really working and none of them have an API.
So i thought to develop a pure python small library not using external software (like *ImageMagick*) to perform this operations.

## Features
- Reads *.ICO* and *.CUR.*
   - Supports multi-sized RGBA 32-bit and RGB 24-bit icon and cursor files.
   - Checks if the image AND mask is correct, otherwise is recomputed if needs.
   - Easy export in other image formats.
   
- Writes *.ICO* from a set of all supported by PIL image formats.
   - Can be generated *.ICO* multi-sized.
   - Gives info messages about conversion process.
   - Automatically resizes input images to the nearest standard icon size.
   - Supports *forced* or *raw* bit per pixel conversion.
   - Makes conversion for different color depths, with or not alpha channel / trasparency.

## Requirements
 *Python 3.5+*,  *PIL (Pillow) 3.3.1+*

## Usage examples
#### How to read an *.ICO*.
`FromIcoCur( ... )` returns a list of lists containing each image stored in *.ICO*:
[ [PIL_object_0, total_number_of_images, width_0, height_0, hotspotX_0, hotspotY_0],...,[PIL_object_N, total_number_of_images, width_N, height_N, hotspotX_N, hotspotY_N] ].
```python
>>> path = '~/path/folder/icons/test_multisized_icon.ico'
>>> ico_readed, log_err = READER().FromIcoCur( path, rebuild = False )
>>> log_err
''
>>> ico_readed
[[<PIL.Image.Image image mode=RGBA size=64x64 at 0x7F096AA93BE0>, 4, 64, 64, 1, 32], [<PIL.Image.Image image mode=RGBA size=48x48 at 0x7F096AA93C50>, 4, 48, 48, 1, 32], [<PIL.Image.Image image mode=RGBA size=32x32 at 0x7F096AA93CC0>, 4, 32, 32, 1, 32], [<PIL.Image.Image image mode=RGBA size=16x16 at 0x7F096AA93D30>, 4, 16, 16, 1, 32]]
```
#### How to export after *.ICO* reading.
```python
>>> ico_readed[0][0].save('~/path/folder/export/64x64.png', 'PNG')
>>> ico_readed[1][0].save('~/path/folder/export/48x48.bmp', 'BMP')
```
#### How to write an *.ICO*.
`ToIco( ... )` returns a list containing info messages for each conversion.
```python
>>> forced_bpp_conversion = False
>>> log_mess = WRITER.ToIco( forced_bpp_conversion, [['~/path/folder/pngs/test.png']], ['~/path/folder/icos/test.ico'] )
>>> log_mess
['~/path/folder/pngs/test.png with mode "RGBA" have bpp = 32 bit --> Successfully wrote icon to ~/path/folder/icos/test.ico.']
```
#### How to write more *.ICOs*.
```python
>>> forced_bpp_conversion = False
>>> logs_mess = WRITER.ToIco( forced_bpp_conversion , [ ['~/path/folder/pngs/test0.png', '~/path/folder/pngs/test1.png'], 
                                                         ['~/path/folder/pngs/test2.png']
                                                       ], 
                                                       ['~/path/folder/icos/test0and1.ico', '~/path/folder/icos/test2.ico'] )
>>> logs_mess[0]
'~/path/folder/pngs/test0.png with mode "RGBA" have bpp = 32 bit and size = 32 x 32; ~/path/folder/pngs/test1.png with mode "RGBA" have bpp = 32 bit and size = 16 x 16 --> Successfully wrote icon to ~/path/folder/icos/test0and1.ico.'
>>> logs_mess[1]
'~/path/folder/pngs/test2.png with mode "RGBA" have bpp = 32 bit --> Successfully wrote icon to ~/path/folder/icos/test2.ico.
```
#### How to automatize process for folders.
```python
>>> path = '~/path/folder/images/pngs'
>>> pngs = [ [(path + testimage)] for testimage in os.listdir(path) ]
>>> icos = [ (path + testimage).replace('.png','.ico') for testimage in os.listdir(path) ]
>>> forced_bpp_conversion = False
>>> logs_mess = WRITER.ToIco( forced_bpp_conversion, pngs, icos )
```

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/SystemRage/Iconolatry/blob/master/LICENSE) ©  Matteo ℱan


