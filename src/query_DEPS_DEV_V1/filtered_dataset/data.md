1. PACKAGEVERSIONS

来源：DEPS_DEV_V1.DEPS_DEV_V1.PACKAGEVERSIONS
在 SQL 中用到的列：

"Name" — 包名

"Version" — 版本号

"VersionInfo" — 用于解析 "Ordinal"（排序最新版本）和 "IsRelease"（筛选发布版本）

2. PACKAGEVERSIONTOPROJECT

来源：DEPS_DEV_V1.DEPS_DEV_V1.PACKAGEVERSIONTOPROJECT
在 SQL 中用到的列：

"Name" — 包名（和 PACKAGEVERSIONS.Name 匹配）

"Version" — 版本号（和 PACKAGEVERSIONS.Version 匹配）

"System" — 系统类型（SQL 里限制为 'NPM'，虽然你现在可以去掉这个限制）

"ProjectType" — 项目类型（SQL 里限制 'GITHUB'，并且用于和 PROJECTS.Type 匹配）

"ProjectName" — 项目名（用于和 PROJECTS.Name 匹配）

3. PROJECTS

来源：DEPS_DEV_V1.DEPS_DEV_V1.PROJECTS
在 SQL 中用到的列：

"Type" — 项目类型（和 PACKAGEVERSIONTOPROJECT.ProjectType 匹配）

"Name" — 项目名（和 PACKAGEVERSIONTOPROJECT.ProjectName 匹配）

"StarsCount" — 用于排序（SQL 最终按这个字段降序）