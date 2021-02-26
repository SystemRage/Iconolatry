# Iconolatry
> *Advanced Icon Converter*

## Why
There are several online converters, icon makers and favicon generators that can 
transform image formats in `.ico` files or to achieve reverse process,
but only a few of them are really working and none of these provides an API.
So i developped a pure python small library, not using external software (like *ImageMagick*), 
to perform the above operations.

## Features
- Gives detailed info about conversion process.
- You can use it as bare module inside your projects or running it with CLI commands. 

- Reads `.ico` and `.cur` formats:
   - You can decode a single icon / cursor, a list of icon / cursor(s), a folder, a list of folders, or mixing...
   - You can decode icon / cursor(s) as bytes stream(s) too.
   - You can select output paths, output file names, output file formats (all those supported by *PIL*) for every conversion process.
   - Supports decoding multi-size and / or multi-depth icons.
   - Checks if the image *AND* mask is correct, otherwise is recomputed if needs.

- Writes `.ico` and `.cur` using a set of images (whose formats are supported by *PIL*):
   - You can convert a single image, a list of images, a folder, a list of folders, or mixing...
   - You can select output paths, output file names, output file formats (`.ico`, `.cur`) for every conversion process.
   - You can generate `.ico` multi-format (packing many images with different sizes and depths).
   - You can provide fixed resize values or automatically let to resize input images to the nearest standard icon size.
   - You can provide hotspots for `.cur` conversions.
   - You can provide custom palettes to apply during conversion (for indexed images).

## Requirements
   - `Python 3+`
   - `PIL (Pillow)`

## Options

### Encoder

|    Parameter      | CLI |       Type      |                                      Description                                                    |
|-------------------|-----|-----------------|-----------------------------------------------------------------------------------------------------|
| `paths_images`    | `-i`| list of lists   | every list can contain one/more image(s) path(s) and/or one/more folder image(s) path(s) to convert |
| `paths_icocur`    | `-o`| list            | contains output path(s) for every resulting conversion. If isn't defined, working directory is used |
| `names_icocur`    | `-n`| list            | contains output name(s) for every resulting conversion. If `paths_images` contains a *folder path* and corresponding `names_icocur` is defined, a multi-`.ico` is created, otherwise every image in *folder path* is converted to a single `.ico`/`.cur` |
| `formats_icocur`  | `-f`| list            | contains format(s) for every resulting conversion (*'.ico'* or *'.cur'*). If `.cur`, can be specified hotspot x (integer) and hotspot y (integer) using a tuple; example: *('.cur', 2, 5)* |
| `type_resize`     | `-r`| string or tuple | with *'up256_prop'* dimensions >256 pixels are resized keeping global image aspect ratio, with *'up256_no_prop'* dimensions >256 pixels are resized without keeping global image aspect ratio, with *'square'* dimensions are resized to nearest            square standard size, with a tuple *(width, height)* for a custom resize |
| `custom_palettes` | `-p`| dict            | the key is a tuple *(mode, bitdepth)*, the value can be a list of RGB tuples *[(R1,G1,B1),...,(Rn,Bn,Gn)]* (usual palette format) or a flat list *[V1,V2,...,Vn]* (compact format for grayscale palette) or a `.gpl` file path |

### Decoder

|    Parameter     | CLI | Type |                                      Description                                                  |
|------------------|-----|------|---------------------------------------------------------------------------------------------------|
| `paths_icocurs`  | `-i`| list | contains one/more icon/cursor(s) path(s) and/or one/more folder icon/cursor(s) path(s) to convert |
| `paths_image`    | `-o`| list | contains output path(s) for every resulting conversion. If isn't defined, working directory is used |
| `names_image`    | `-n`| list | contains output name(s) for every resulting conversion |
| `formats_image`  | `-f`| list | contains format(s) for every resulting conversion (all saving PIL formats) |
| `rebuild`        | `-u`| bool | if *True*, recompute mask from the alpha channel data |

## Usage Examples

### How to write an `.ico`.
```python
>>> conv = Encode([['/path/input/test0.png']], paths_icocur = ['/path/output'], names_icocur = ['myname'], formats_icocur = ['.ico'],
                  type_resize = (48, 28))
>>> conv.all_icocur_written
{'/path/output/myname.ico': [{'file': '/path/input/test0.png', 'mode': 'grayscale', 'depth': 1, 'size': '32 x 32', 'resize': '48 x 28'}]}
```
```
python3 Iconolatry.py encode -i /path/input/test0.png -o /path/output -n myname -f .ico -r "(48, 28)"
```

### How to write a `.cur`.
```python
>>> conv = Encode([['/path/input/test0.png']], paths_icocur = ['/path/output'], names_icocur = ['myname'], formats_icocur = [('.cur', 2, 5)],
                  custom_palettes = {('1', 1) : '/path/palettes/custom1bit.gpl')
>>> conv.all_icocur_written
{'/path/output/myname.cur': [{'file': '/path/input/test0.png', 'mode': 'grayscale', 'depth': 1, 'size': '32 x 32'}]}
```
```
python3 Iconolatry.py encode -i /path/input/test0.png -o /path/output -n myname -f "('.cur', 2, 5)" -p "{('1', 1) : '/path/palettes/custom1bit.gpl'}"
```

#### How to write a multi-`.ico`.
```python
>>> conv = Encode([['/path/input/test0.png', '/path/input/test1.bmp', '/path/input/test2.jpg']], paths_icocur = [''],
                  names_icocur = [''], formats_icocur = ['.ico'])
>>> conv.all_icocur_written
{'/path/working/directory/multi.ico': [{'file': '/path/input/test0.png', 'mode': 'grayscale', 'depth': 1, 'size': '32 x 32'}, {'file': '/path/input/test1.bmp', 'mode': 'grayscale', 'depth': 4, 'size': '48 x 48'}, {'file': '/path/input/test2.jpg', 'mode': 'grayscale', 'depth': 8, 'size': '16 x 16'}]
}
```
Note how the *multi* name is auto-assigned because `names_icocur` isn't setted.
```
python3 Iconolatry.py encode -i /path/input/test0.png /path/input/test1.bmp /path/input/test2.jpg -f .ico
```

#### How to write more `.ico`s and/or `.cur`s together.
```python
>>> conv = Encode([['/path/input/test0.png', '/path/input/test1.png'], ['/path/input/test2.png']], 
                  paths_icocur = ['/path/outputA', '/path/outputB'],
                  names_icocur = ['test01', 'test2'],
                  formats_icocur = ['.ico', '.cur'])
>>> conv.all_icocur_written
{'/path/outputA/test01.ico': [{'file': '/path/input/test0.png', 'mode': 'grayscale', 'depth': 1, 'size': '32 x 32'}, {'file': '/path/input/test1.png', 'mode': 'grayscale', 'depth': 4, 'size': '48 x 48'}], 
'/path/outputB/test2.cur': [{'file': '/path/input/test2.png', 'mode': 'grayscale', 'depth': 8, 'size': '16 x 16'}]
}
```
```
python3 Iconolatry.py encode -i /path/input/test0.png /path/input/test1.png -o /path/outputA -i /path/input/test2.png -o /path/outputB
-n test01 test2 -f .ico .cur
```

#### How to encode image folders.
```python
>>> conv = Encode([['/path/input/folder'], ['/path/input/folder']], paths_icocur = ['/path/outputA', '/path/outputB'], 
                    names_icocur = ['mymultico', ''],
                    formats_icocur = ['.ico', '.cur'])
>>> conv.all_icocur_written
{'/path/outputA/mymulti.ico': [{'file': '/path/input/folder/test0.png', 'mode': 'grayscale', 'depth': 1, 'size': '32 x 32'}, {'file': '/path/input/folder/test1.png', 'mode': 'grayscale', 'depth': 4, 'size': '48 x 48'}, {'file': '/path/input/folder/test2.png', 'mode': 'grayscale', 'depth': 8, 'size': '16 x 16'}],
'/path/outputB/test0.cur': [{'file': '/path/input/folder/test0.png', 'mode': 'grayscale', 'depth': 1, 'size': '32 x 32', 'hotspot_x': 0, 'hotspot_y': 0}], 
'/path/outputB/test1.cur': [{'file': '/path/input/folder/test1.png', 'mode': 'grayscale', 'depth': 4, 'size': '48 x 48', 'hotspot_x': 0, 'hotspot_y': 0}], 
'/path/outputB/test2.cur': [{'file': '/path/input/folder/test2.png', 'mode': 'grayscale', 'depth': 8, 'size': '16 x 16', 'hotspot_x': 0, 'hotspot_y': 0}]
}
```
```
python3 Iconolatry.py encode -i /path/input/folder -o /path/outputA -n mymultico -f .ico -i /path/input/folder -o /path/outputB -f .cur
```

#### How to read more `.ico` and/or `.cur` together.
```python
>>> conv = Decode(['/path/input/cursor.cur', '/path/input/multicon.ico'], paths_image = [''], names_image = [''], formats_image = ['.png', '.bmp'])

>>> conv.all_icocur_readed
{'/path/input/cursor.cur': {'image_0': {'im_obj': <PIL.Image.Image image mode=RGBA size=32x32 at 0x7FDEF936C780>, 'depth': 32, 'hotspot_x': 0, 'hotspot_y': 0, 'saved': '/path/working/directory/cursor.png'}}, 
'/path/input/multicon.ico': {'image_0': {'im_obj': <PIL.Image.Image image mode=RGBA size=16x16 at 0x7FDEF936C860>, 'depth': 1, 'saved': '/path/working/directory/multicon_0.bmp'}, 'image_1': {'im_obj': <PIL.Image.Image image mode=RGBA size=32x32 at 0x7FDEF936C630>, 'depth': 24, 'saved': '/path/working/directory/multicon_1.bmp'}, 'image_2': {'im_obj': <PIL.Image.Image image mode=RGBA size=48x48 at 0x7FDEF936C4A8>, 'depth': 32, 'saved': '/path/working/directory/multicon_2.bmp'}}
}
```
```
python3 Iconolatry.py decode -i /path/input/cursor.cur /path/input/multicon.ico -f .png .bmp
```

#### How to decode image folders.
```python
>>> conv = Decode(['/path/input/folder'], paths_image = ['/path/outputA'], names_image = ['customname'], rebuild = True)

>>> conv.all_icocur_readed
{'/path/input/folder/test0.cur': {'image_0': {'im_obj': <PIL.Image.Image image mode=RGBA size=16x16 at 0x7FDFDE8E52E8>, 'depth': 1, 'hotspot_x': 0, 'hotspot_y': 0, 'saved': '/path/outputA/customname_0.png'}}, 
'/path/input/folder/test1.cur': {'image_0': {'im_obj': <PIL.Image.Image image mode=RGBA size=48x48 at 0x7FDFDE8E5438>, 'depth': 32, 'hotspot_x': 0, 'hotspot_y': 0, 'saved': '/path/outputA/customname_1.png'}}, 
'/path/input/folder/test2.cur': {'image_0': {'im_obj': <PIL.Image.Image image mode=RGBA size=32x32 at 0x7FDFDE8E5860>, 'depth': 24, 'hotspot_x': 0, 'hotspot_y': 0, 'saved': '/path/outputA/customname_2.png'}}, 
'/path/input/folder/testymulti.ico': {'image_0': {'im_obj': <PIL.Image.Image image mode=RGBA size=16x16 at 0x7FDFDE8E5240>, 'depth': 1, 'saved': '/path/outputA/customname_3.png'}, 'image_1': {'im_obj': <PIL.Image.Image image mode=RGBA size=48x48 at 0x7FDFDE8E5B70>, 'depth': 32, 'saved': '/path/outputA/customname_4.png'}, 'image_2': {'im_obj': <PIL.Image.Image image mode=RGBA size=32x32 at 0x7FDFDE8E5C18>, 'depth': 24, 'saved': '/path/outputA/customname_5.png'}}
}
```
```
python3 Iconolatry.py decode -i /path/input/folder -o /path/outputA -n customname -u
```

## License
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/SystemRage/Iconolatry/blob/master/LICENSE) ©  Matteo ℱan
