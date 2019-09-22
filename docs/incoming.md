# Deferred modifications -- Track changes

## vls

### Annoucement

When no data source was provided, VisiData presented the [DirSheet](/docs/assets/DirSheet.png) as the opening sheet. Similar to vim, this interface permits the interactive loading of files, by moving the cursor to the row which references it and pressing `Enter`.

From v1.2 to v1.5.2, the DirSheet became more [powerful](https://www.youtube.com/watch?v=prdyXM6-FSc). Files became first-class data citizens and users could use classic vd data manipulation commands to (bulk) rename and delete files. Once made, changes were deferred until commited to with `Ctrl+S`. They were then reflected in the filesystem itself.

It became apparent that the write-mode of the DirSheet was a conceptually separate tool, even if the interface was identical. Data sheets and filesystem editing are kind of two radically different use cases.

So from 2.-2 and on, it was decided to move the filesystem manipulation part of VisiData into the entry point **vls**.

### Description (How to do file system manipulation with VisiData)

**vls** is a tool which combines file system manipulation with the power of the VisiData interface.

Changes can be made to and rows can be deleted. These changes will be colored to signify that they are **deferred**. Until they are committed to, these changes are merely a proposal, and `Ctrl+R` clears all of them. Comitting with `Ctrl+S` results in them being reflected in the filesystem. Deleted rows trigger deletion of those respective files, and `filename` edits bulk rename all of the referenced files.

----
Warning: Those files really do get deleted. Approach with caution before you commit!
----

#### How to bulk rename files

#### How to bulk delete files


#### Installation instructions
To play with it, install VisiData >= 2.0, and then type `vls`.
