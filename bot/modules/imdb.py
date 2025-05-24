from contextlib import suppress
from re import IGNORECASE, findall, search

from imdb import Cinemagoer
from pycountry import countries as conn
from pyrogram.errors import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty

from ..core.tg_client import TgClient
from ..core.config_manager import Config
from ..helper.ext_utils.status_utils import get_readable_time
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    send_message,
    edit_message,
    delete_message,
)

imdb = Cinemagoer()

IMDB_GENRE_EMOJI = {
    "Action": "🚀",
    "Adult": "🔞",
    "Adventure": "🌋",
    "Animation": "🎠",
    "Biography": "📜",
    "Comedy": "🪗",
    "Crime": "🔪",
    "Documentary": "🎞",
    "Drama": "🎭",
    "Family": "👨‍👩‍👧‍👦",
    "Fantasy": "🫧",
    "Film Noir": "🎯",
    "Game Show": "🎮",
    "History": "🏛",
    "Horror": "🧟",
    "Musical": "🎻",
    "Music": "🎸",
    "Mystery": "🧳",
    "News": "📰",
    "Reality-TV": "🖥",
    "Romance": "🥰",
    "Sci-Fi": "🌠",
    "Short": "📝",
    "Sport": "⛳",
    "Talk-Show": "👨‍🍳",
    "Thriller": "🗡",
    "War": "⚔",
    "Western": "🪩",
}
LIST_ITEMS = 4


async def imdb_search(_, message):
    if " " in message.text:
        k = await send_message(message, "<i>Searching IMDB ...</i>")
        title = message.text.split(" ", 1)[1]
        user_id = message.from_user.id
        buttons = ButtonMaker()
        if result := search(r"imdb\.com/title/tt(\d+)", title, IGNORECASE):
            movieid = result.group(1)
            if movie := imdb.get_movie(movieid):
                buttons.data_button(
                    f"🎬 {movie.get('title')} ({movie.get('year')})",
                    f"imdb {user_id} movie {movieid}",
                )
            else:
                return await edit_message(k, "<i>No Results Found</i>")
        else:
            movies = get_poster(title, bulk=True)
            if not movies:
                return edit_message(
                    "<i>No Results Found</i>, Try Again or Use <b>Title ID</b>", k
                )
            for movie in movies:  # Refurbished Soon !!
                buttons.data_button(
                    f"🎬 {movie.get('title')} ({movie.get('year')})",
                    f"imdb {user_id} movie {movie.movieID}",
                )
        buttons.data_button("🚫 Close 🚫", f"imdb {user_id} close")
        await edit_message(
            k, "<b><i>Search Results found on IMDb.com</i></b>", buttons.build_menu(1)
        )
    else:
        await send_message(
            message,
            "<i>Send Movie / TV Series Name along with /imdb Command or send IMDB URL</i>",
        )


def get_poster(query, bulk=False, id=False, file=None):
    if not id:
        query = (query.strip()).lower()
        title = query
        year = findall(r"[1-2]\d{3}$", query, IGNORECASE)
        if year:
            year = list_to_str(year[:1])
            title = (query.replace(year, "")).strip()
        elif file is not None:
            year = findall(r"[1-2]\d{3}", file, IGNORECASE)
            if year:
                year = list_to_str(year[:1])
        else:
            year = None
        movieid = imdb.search_movie(title.lower(), results=10)
        if not movieid:
            return None
        if year:
            filtered = (
                list(filter(lambda k: str(k.get("year")) == str(year), movieid))
                or movieid
            )
        else:
            filtered = movieid
        movieid = (
            list(filter(lambda k: k.get("kind") in ["movie", "tv series"], filtered))
            or filtered
        )
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = query
    movie = imdb.get_movie(movieid)
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    plot = movie.get("plot")
    plot = plot[0] if plot and len(plot) > 0 else movie.get("plot outline")
    if plot and len(plot) > 300:
        plot = f"{plot[:300]}..."
    return {
        "title": movie.get("title"),
        "trailer": movie.get("videos"),
        "votes": movie.get("votes"),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get("box office"),
        "localized_title": movie.get("localized title"),
        "kind": movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str(
            [get_readable_time(int(run) * 60) for run in movie.get("runtimes", "0")]
        ),
        "countries": list_to_hash(movie.get("countries"), True),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_hash(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer": list_to_str(movie.get("writer")),
        "producer": list_to_str(movie.get("producer")),
        "composer": list_to_str(movie.get("composer")),
        "cinematographer": list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        "release_date": date,
        "year": movie.get("year"),
        "genres": list_to_hash(movie.get("genres"), emoji=True),
        "poster": movie.get("full-size cover url"),
        "plot": plot,
        "rating": str(movie.get("rating")) + " / 10",
        "url": f"https://www.imdb.com/title/tt{movieid}",
        "url_cast": f"https://www.imdb.com/title/tt{movieid}/fullcredits#cast",
        "url_releaseinfo": f"https://www.imdb.com/title/tt{movieid}/releaseinfo",
    }


def list_to_str(k):
    if not k:
        return ""
    elif len(k) == 1:
        return str(k[0])
    elif LIST_ITEMS:
        k = k[: int(LIST_ITEMS)]
        return " ".join(f"{elem}," for elem in k)[:-1] + " ..."
    else:
        return " ".join(f"{elem}," for elem in k)[:-1]


def list_to_hash(k, flagg=False, emoji=False):
    listing = ""
    if not k:
        return ""
    elif len(k) == 1:
        if not flagg:
            if emoji:
                return str(
                    IMDB_GENRE_EMOJI.get(k[0], "")
                    + " #"
                    + k[0].replace(" ", "_").replace("-", "_")
                )
            return str("#" + k[0].replace(" ", "_").replace("-", "_"))
        try:
            conflag = (conn.get(name=k[0])).flag
            return str(f"{conflag} #" + k[0].replace(" ", "_").replace("-", "_"))
        except AttributeError:
            return str("#" + k[0].replace(" ", "_").replace("-", "_"))
    elif LIST_ITEMS:
        k = k[: int(LIST_ITEMS)]
        for elem in k:
            ele = elem.replace(" ", "_").replace("-", "_")
            if flagg:
                with suppress(AttributeError):
                    conflag = (conn.get(name=elem)).flag
                    listing += f"{conflag} "
            if emoji:
                listing += f"{IMDB_GENRE_EMOJI.get(elem, '')} "
            listing += f"#{ele}, "
        return f"{listing[:-2]}"
    else:
        for elem in k:
            ele = elem.replace(" ", "_").replace("-", "_")
            if flagg:
                conflag = (conn.get(name=elem)).flag
                listing += f"{conflag} "
            listing += f"#{ele}, "
        return listing[:-2]


async def imdb_callback(_, query):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
    elif data[2] == "movie":
        await query.answer()
        imdb = get_poster(query=data[3], id=True)
        buttons = ButtonMaker()
        if imdb["trailer"]:
            if isinstance(imdb["trailer"], list):
                buttons.url_button("▶️ IMDb Trailer ", imdb["trailer"][-1])
                imdb["trailer"] = list_to_str(imdb["trailer"])
            else:
                buttons.url_button("▶️ IMDb Trailer ", imdb["trailer"])
        buttons.data_button("🚫 Close 🚫", f"imdb {user_id} close")
        buttons = buttons.build_menu(1)
        template = ""
        # if int(data[1]) in user_data and user_data[int(data[1])].get('imdb_temp'):
        #    template = user_data[int(data[1])].get('imdb_temp')
        # if not template:
        template = Config.IMDB_TEMPLATE
        if imdb and template != "":
            cap = template.format(**imdb, **locals())
        else:
            cap = "No Results"
        if imdb.get("poster"):
            try:
                await TgClient.bot.send_photo(
                    chat_id=query.message.reply_to_message.chat.id,
                    caption=cap,
                    photo=imdb["poster"],
                    reply_to_message_id=query.message.reply_to_message.id,
                    reply_markup=buttons,
                )
            except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                poster = imdb.get("poster").replace(".jpg", "._V1_UX360.jpg")
                await send_message(message.reply_to_message, cap, buttons, photo=poster)
        else:
            await send_message(
                message.reply_to_message,
                cap,
                buttons,
                "https://telegra.ph/file/5af8d90a479b0d11df298.jpg",
            )
        await delete_message(message)
    else:
        await query.answer()
        await delete_message(message, message.reply_to_message)
