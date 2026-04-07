from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QPainter


@dataclass(slots=True)
class TileDefinition:
	id: int
	name: str
	color: str
	solid: bool = False


@dataclass(slots=True)
class SpawnPoint:
	x: int
	y: int


@dataclass(slots=True)
class LevelData:
	name: str
	width: int
	height: int
	tile_size: int
	tiles: list[list[int]]
	tile_types: dict[int, TileDefinition]
	player_spawn: SpawnPoint


class LevelValidationError(ValueError):
	pass


class LevelHandler:
	"""Load, validate and use JSON-defined tile maps for a 2D PyQt game."""

	def __init__(self, levels_dir: Path | None = None):
		self._root = Path(__file__).resolve().parents[2]
		self.levels_dir = levels_dir or (self._root / "levels")

	@staticmethod
	def generate_template(
		name: str,
		width: int = 20,
		height: int = 12,
		tile_size: int = 32,
		fill_tile: int = 0,
	) -> dict:
		"""Generate a valid JSON level template that can be saved directly."""
		tiles = [[fill_tile for _ in range(width)] for _ in range(height)]

		return {
			"name": name,
			"meta": {
				"width": width,
				"height": height,
				"tile_size": tile_size,
			},
			"tile_types": {
				"0": {"name": "empty", "color": "#101010", "solid": False},
				"1": {"name": "ground", "color": "#2E8B57", "solid": True},
				"2": {"name": "hazard", "color": "#CC3333", "solid": True},
			},
			"layers": {
				"tiles": tiles,
			},
			"entities": {
				"player_spawn": {"x": 1, "y": 1},
			},
		}

	def create_level_file(self, filename: str, level_data: dict) -> Path:
		"""Write a level JSON file and return its path."""
		self.levels_dir.mkdir(parents=True, exist_ok=True)
		path = self.levels_dir / filename

		with path.open("w", encoding="utf-8") as file:
			json.dump(level_data, file, indent=4, ensure_ascii=False)

		return path

	def load_level(self, level_name: str) -> LevelData:
		"""Load and validate one level file by name, e.g. 'level_001.json'."""
		level_path = self.levels_dir / level_name

		if not level_path.exists():
			raise FileNotFoundError(f"Level not found: {level_path}")

		with level_path.open("r", encoding="utf-8") as file:
			data = json.load(file)

		return self._validate_and_build(data)

	def draw_level(self, painter: QPainter, level: LevelData) -> None:
		"""Draw the tile grid from level data using the configured tile colors."""
		for row_idx, row in enumerate(level.tiles):
			for col_idx, tile_id in enumerate(row):
				tile = level.tile_types[tile_id]
				color = QColor(tile.color)
				painter.fillRect(
					col_idx * level.tile_size,
					row_idx * level.tile_size,
					level.tile_size,
					level.tile_size,
					color,
				)

	def collision_rects(self, level: LevelData) -> list[QRect]:
		"""Return solid tile rectangles for fast collision checks."""
		rects: list[QRect] = []
		for row_idx, row in enumerate(level.tiles):
			for col_idx, tile_id in enumerate(row):
				if level.tile_types[tile_id].solid:
					rects.append(
						QRect(
							col_idx * level.tile_size,
							row_idx * level.tile_size,
							level.tile_size,
							level.tile_size,
						)
					)
		return rects

	def _validate_and_build(self, data: dict) -> LevelData:
		required_top_level = {"name", "meta", "tile_types", "layers", "entities"}
		missing = required_top_level - set(data.keys())
		if missing:
			raise LevelValidationError(f"Missing top-level keys: {sorted(missing)}")

		meta = data["meta"]
		width = int(meta["width"])
		height = int(meta["height"])
		tile_size = int(meta["tile_size"])

		if width <= 0 or height <= 0 or tile_size <= 0:
			raise LevelValidationError("width, height and tile_size must be > 0")

		raw_types = data["tile_types"]
		tile_types: dict[int, TileDefinition] = {}

		for tile_id, tile_data in raw_types.items():
			num_id = int(tile_id)
			tile_types[num_id] = TileDefinition(
				id=num_id,
				name=str(tile_data["name"]),
				color=str(tile_data["color"]),
				solid=bool(tile_data.get("solid", False)),
			)

		tiles = data["layers"]["tiles"]
		if len(tiles) != height:
			raise LevelValidationError(
				f"Expected {height} rows in tiles, got {len(tiles)}"
			)

		for row in tiles:
			if len(row) != width:
				raise LevelValidationError(
					f"Each row in tiles must have width {width}, got {len(row)}"
				)
			for tile_id in row:
				if tile_id not in tile_types:
					raise LevelValidationError(
						f"Tile id {tile_id} is used in tiles but missing in tile_types"
					)

		raw_spawn = data["entities"]["player_spawn"]
		spawn = SpawnPoint(x=int(raw_spawn["x"]), y=int(raw_spawn["y"]))
		if not (0 <= spawn.x < width and 0 <= spawn.y < height):
			raise LevelValidationError("player_spawn must be inside map bounds")

		return LevelData(
			name=str(data["name"]),
			width=width,
			height=height,
			tile_size=tile_size,
			tiles=tiles,
			tile_types=tile_types,
			player_spawn=spawn,
		)
