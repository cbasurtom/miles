# miles

miles is a Python homebrew webcrawler originally designed as a project for my [Systems Programming](https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/) course. It was the first program I designed which had an actually diverse amount of considerations, from web access and download to file management and even concurrency. Extensively reading Python libraries such as `concurrent`, `urlib`, `requests`, `re`, among others, opened my eyes to the true power of Python.

The name, naturally, alludes to quite a famous crawler.

## Usage

```python
'''Usage: miles.py [-d DESTINATION -n CPUS -f FILETYPES] URL

Crawl the given URL for the specified FILETYPES and download the files to the
DESTINATION folder using CPUS cores in parallel.

    -d DESTINATION      Save the files to this folder (default: {DESTINATION})
    -n CPUS             Number of CPU cores to use (default: {CPUS})
    -f FILETYPES        List of file types: jpg, mp3, pdf, png (default: all)

Multiple FILETYPES can be specified in the following manner:

    -f jpg,png
    -f jpg -f png'''
```

## Licence

[MIT](https://choosealicense.com/licenses/mit/)
