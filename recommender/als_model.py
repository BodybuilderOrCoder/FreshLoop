"""ALS collaborative filtering engine for FreshLoop grocery recommendations."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from implicit.als import AlternatingLeastSquares
from scipy.sparse import coo_matrix, csr_matrix

from . import config


@dataclass
class ALSRecommender:
    """Train an implicit-feedback ALS model and return ranked product IDs."""

    factors: int = 32
    regularization: float = 0.05
    iterations: int = 20
    alpha: float = 20.0
    random_state: int = 42

    model: AlternatingLeastSquares | None = field(
        default=None, init=False, repr=False
    )
    user_to_index: dict[str, int] = field(
        default_factory=dict, init=False
    )
    product_to_index: dict[str, int] = field(
        default_factory=dict, init=False
    )
    index_to_product: list[str] = field(
        default_factory=list, init=False
    )
    user_items: csr_matrix | None = field(
        default=None, init=False, repr=False
    )
    interactions: pd.DataFrame | None = field(
        default=None, init=False, repr=False
    )
    popular_product_ids: list[str] = field(
        default_factory=list, init=False
    )

    def fit(self, interactions: pd.DataFrame) -> "ALSRecommender":
        """Fit ALS using user_id, product_id and positive implicit_rating."""
        required = {"user_id", "product_id", "implicit_rating"}
        missing = required.difference(interactions.columns)

        if missing:
            raise ValueError(
                f"Missing required interaction columns: {sorted(missing)}"
            )

        data = interactions[
            ["user_id", "product_id", "implicit_rating"]
        ].copy()

        data = data.dropna(subset=["user_id", "product_id"])
        data["user_id"] = data["user_id"].astype(str).str.strip()
        data["product_id"] = data["product_id"].astype(str).str.strip()
        data["implicit_rating"] = pd.to_numeric(
            data["implicit_rating"], errors="coerce"
        )

        valid = (
            data["user_id"].ne("")
            & data["product_id"].ne("")
            & np.isfinite(data["implicit_rating"])
            & data["implicit_rating"].gt(0)
        )
        data = data.loc[valid]

        if data.empty:
            raise ValueError(
                "ALS training requires at least one positive interaction."
            )

        # Combine repeated pairs into one confidence value.
        data = (
            data.groupby(["user_id", "product_id"], as_index=False)
            .agg(implicit_rating=("implicit_rating", "sum"))
        )

        users = sorted(data["user_id"].unique().tolist())
        products = sorted(data["product_id"].unique().tolist())

        self.user_to_index = {
            user_id: index for index, user_id in enumerate(users)
        }
        self.product_to_index = {
            product_id: index for index, product_id in enumerate(products)
        }
        self.index_to_product = products
        self.interactions = data.reset_index(drop=True)

        row_indices = data["user_id"].map(self.user_to_index).to_numpy(
            dtype=np.int32
        )
        column_indices = data["product_id"].map(
            self.product_to_index
        ).to_numpy(dtype=np.int32)
        confidence = data["implicit_rating"].to_numpy(dtype=np.float32)

        self.user_items = coo_matrix(
            (
                confidence,
                (row_indices, column_indices),
            ),
            shape=(len(users), len(products)),
            dtype=np.float32,
        ).tocsr()

        popularity = (
            data.groupby("product_id", as_index=False)
            .agg(popularity=("implicit_rating", "sum"))
            .sort_values(
                ["popularity", "product_id"],
                ascending=[False, True],
                kind="stable",
            )
        )
        self.popular_product_ids = popularity["product_id"].tolist()

        self.model = AlternatingLeastSquares(
            factors=self.factors,
            regularization=self.regularization,
            alpha=self.alpha,
            iterations=self.iterations,
            random_state=self.random_state,
            num_threads=1,
            use_gpu=False,
        )
        self.model.fit(self.user_items, show_progress=False)

        return self

    def recommend(
        self,
        user_id,
        top_k: int = config.TOP_K,
        filter_seen: bool = False,
    ) -> list[dict]:
        """Return ranked recommendations, with popularity fallback.

        filter_seen defaults to False because repeat purchases are relevant
        for a grocery recommender. Set it to True to exclude training items.
        """
        if self.model is None or self.user_items is None:
            raise RuntimeError("Call fit() before requesting recommendations.")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        normalized_user = str(user_id)
        user_index = self.user_to_index.get(normalized_user)

        seen_products: set[str] = set()
        results: list[dict] = []
        selected_products: set[str] = set()

        if user_index is not None:
            seen_indices = self.user_items[user_index].indices
            seen_products = {
                self.index_to_product[int(index)]
                for index in seen_indices
            }

            item_indices, scores = self.model.recommend(
                user_index,
                self.user_items[user_index],
                N=min(top_k, len(self.index_to_product)),
                filter_already_liked_items=filter_seen,
            )

            for item_index, score in zip(item_indices, scores):
                product_id = self.index_to_product[int(item_index)]

                if filter_seen and product_id in seen_products:
                    continue

                if product_id in selected_products:
                    continue

                results.append(
                    {
                        "product_id": product_id,
                        "score": round(float(score), 6),
                        "source": "als",
                    }
                )
                selected_products.add(product_id)

        # Cold-start fallback, or pad if ALS produces too few candidates.
        for product_id in self.popular_product_ids:
            if len(results) >= top_k:
                break

            if product_id in selected_products:
                continue

            if filter_seen and product_id in seen_products:
                continue

            results.append(
                {
                    "product_id": product_id,
                    "score": 0.0,
                    "source": "popular",
                }
            )
            selected_products.add(product_id)

        for rank, item in enumerate(results, start=1):
            item["rank"] = rank

        return results
