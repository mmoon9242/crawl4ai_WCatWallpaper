# 白猫プロジェクト NEW WORLD'S 公式サイト Wallpaper downloader

A program for downloading wallpapers from the posts on the [白猫プロジェクト NEW WORLD'S 公式サイト](https://colopl.co.jp/shironekoproject/news).

## start & end posts mode

Download wallpapers inside the posts from `start ID` to `end ID` at [白猫プロジェクト NEW WORLD'S 公式サイト](https://colopl.co.jp/shironekoproject/news) .


```python
python ./main.py -start {{0-20}} -end {{0-20}} 
```

### Example

Download wallpapers inside the posts from `0` to `10` at [白猫プロジェクト NEW WORLD'S 公式サイト](https://colopl.co.jp/shironekoproject/news) .

```python
python ./main.py -start 0 -end 10
```

---

## Specify the posts mode

Download wallpapers inside the **specified posts** at [白猫プロジェクト NEW WORLD'S 公式サイト](https://colopl.co.jp/shironekoproject/news) .

```python
python ./main.py -start {{0-20}}
```

### Example

Download wallpapers inside the post with ID `2` at [白猫プロジェクト NEW WORLD'S 公式サイト](https://colopl.co.jp/shironekoproject/news) .

```python
python ./main.py -start 2
```

---

## Posts list mode

Modify `WCatNewsUrlList`, specify the pages you want to fetch, and run `main.py` without parameters.


```python
python ./main.py
```

---