# iDrive API Wrapper

This project is a Python API wrapper for [iDrive](https://github.com/pam-param-pam/I-Drive), 
enabling easy programmatic access to your files and folders stored in iDrive. 
It provides full api coverage(_Soon™_) with methods to fetch, modify, and manage your data without 
manually interacting with the iDrive web interface.

---

## Simple Usage


Here's a quick example to get started with accessing and modifying files and folders:

```python
token = Client.login("login", "password")
client = Client(token)

file = client.get_file("file_id_here")
folder = client.get_folder("folder_id_here")

# Access properties
print(f"File name: {file.name}")
print(f"Folder created: {folder.created}")

# Rename a file
file.rename("new_file_name.txt")

# Move a folder to trash
folder.move_to_trash()

# Restore a folder from trash
folder.restore_from_trash()
```

## UltraDownloader

UltraDownloader is an alternative, high-performance way to download files from iDrive. 

When downloading files via the web interface, each fragment is downloaded sequentially, one after another. 
The backend must first retrieve the fragment from Discord, decrypt it, and then stream it to you. 
This process introduces delays and limits the overall download speed.

Here's the benchmark, tested in **1Gbps** Internet speed:    

| Web interface                       | Achievable Speed | Notes                                                                                                     |
|-------------------------------------|------------------|-----------------------------------------------------------------------------------------------------------|
| Download (discord messages cached)  | up to 50Mb/s     | With discord messages cached, theres no need to ask discord for attachment_url every time                 |
| Download (No cache)                 | 5-15Mb/s         | Having to ask discord for attachment_url + doing things not in parallel significantly slows things down   |
| Upload                              | up to 30Mb/s     | Im not quite sure what slows it down. Theoretically it should allow for faster upload. Perhaps its my ISP |



| Ultra Downloader                   | Achievable Speed       | Notes                                                                                                                                                     |
|------------------------------------|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Download (discord messages cached) | Max ISP download speed | Tweak max_workers param based on your internet speed                                                                                                      |
| Download (No cache)                | Max ISP download speed | This will only work provided you have enough bots available to ask discord for attachment_urls. I use 20 bots and can reach download speeds up to 200Mb/s |
| Upload                             | N/A                    | Coming one day perhaps?                                                                                                                                   |

### How to Use UltraDownloader

- Have a lot of bots assigned.
- The downloader spawns a lot of async tasks to fetch file chunks of files simultaneously.
- Once all chunks are downloaded, they get merged, and decrypted.
- Tweak the `max_workers` setting based on your internet speed.

```python
file = client.get_file("LE8tUWusDAWzejZrKeVwc5", "1")
client.get_ultra_downloader(max_workers=20).download(file) # default 40, ideal for 20 bots && 1Gbps Internet speed 
```