"""Consolidated Monopoly white-box test suite."""

import importlib
import runpy

import pytest

from moneypoly import ui
from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.config import GO_SALARY, INCOME_TAX_AMOUNT, JAIL_FINE
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


def test_property_mortgage_and_unmortgage_branches():
    group = PropertyGroup("G", "g")
    prop = Property("P", 1, 100, 10, group)

    first = prop.mortgage()
    second = prop.mortgage()
    cost = prop.unmortgage()
    second_unmortgage = prop.unmortgage()

    assert first == 50
    assert second == 0
    assert cost == 55
    assert second_unmortgage == 0


def test_property_get_rent_branches_for_normal_and_mortgaged():
    group = PropertyGroup("G", "g")
    p1 = Property("P1", 1, 100, 10, group)
    p2 = Property("P2", 3, 100, 10, group)
    owner = Player("Owner")
    p1.owner = owner
    p2.owner = Player("Other")

    assert p1.get_rent() == 20

    p1.is_mortgaged = True
    assert p1.get_rent() == 0


def test_property_is_available_branches():
    group = PropertyGroup("G", "g")
    prop = Property("P", 1, 100, 10, group)

    assert prop.is_available() is True
    prop.owner = Player("A")
    assert prop.is_available() is False
    prop.owner = None
    prop.is_mortgaged = True
    assert prop.is_available() is False


def test_property_group_counts_and_size():
    group = PropertyGroup("G", "g")
    p1 = Property("P1", 1, 100, 10, group)
    p2 = Property("P2", 3, 100, 10, group)
    a = Player("A")
    b = Player("B")
    p1.owner = a
    p2.owner = b

    counts = group.get_owner_counts()

    assert counts[a] == 1
    assert counts[b] == 1
    assert group.size() == 2


def test_board_tile_type_and_purchasable_branches():
    board = Board()

    assert board.get_tile_type(0) == "go"
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(12) == "blank"
    assert board.is_special_tile(7) is True
    assert board.is_special_tile(1) is False

    prop = board.get_property_at(1)
    assert board.is_purchasable(1) is True
    prop.owner = Player("A")
    assert board.is_purchasable(1) is False


def test_board_owned_and_unowned_queries():
    board = Board()
    player = Player("A")
    prop = board.get_property_at(1)
    prop.owner = player

    owned = board.properties_owned_by(player)
    unowned = board.unowned_properties()

    assert prop in owned
    assert prop not in unowned


def test_bank_pay_out_branches_and_errors():
    bank = Bank()
    start = bank.get_balance()

    assert bank.pay_out(0) == 0
    paid = bank.pay_out(100)
    assert paid == 100
    assert bank.get_balance() == start - 100

    try:
        bank.pay_out(bank.get_balance() + 1)
        assert False, "Expected ValueError for insufficient funds"
    except ValueError:
        assert True


def test_bank_loan_edge_non_positive_is_ignored():
    bank = Bank()
    player = Player("A")
    start = player.balance

    bank.give_loan(player, 0)
    bank.give_loan(player, -10)

    assert player.balance == start
    assert bank.loan_count() == 0


def test_carddeck_draw_peek_and_cycle_branches():
    deck = CardDeck([{"id": 1}, {"id": 2}])

    assert deck.peek()["id"] == 1
    assert deck.cards_remaining() == 2

    c1 = deck.draw()
    c2 = deck.draw()
    c3 = deck.draw()

    assert c1["id"] == 1
    assert c2["id"] == 2
    assert c3["id"] == 1
    assert len(deck) == 2


def test_carddeck_empty_branches_return_none():
    deck = CardDeck([])

    assert deck.draw() is None
    assert deck.peek() is None


def test_player_money_and_bankruptcy_branches():
    player = Player("A")
    player.add_money(50)
    player.deduct_money(100)

    assert player.balance == 1450
    assert player.is_bankrupt() is False

    player.deduct_money(2000)
    assert player.is_bankrupt() is True


def test_player_property_helpers_and_status_line():
    group = PropertyGroup("G", "g")
    prop = Property("P", 1, 100, 10, group)
    player = Player("A")

    player.add_property(prop)
    assert player.count_properties() == 1
    player.remove_property(prop)
    assert player.count_properties() == 0
    assert "A:" in player.status_line()


def test_game_card_handlers_pay_jail_and_jail_free_paths():
    game = Game(["A", "B"])
    player = game.players[0]

    start_player = player.balance
    start_bank = game.bank.get_balance()

    game._apply_card_pay(player, 50)
    assert player.balance == start_player - 50
    assert game.bank.get_balance() == start_bank + 50

    game._apply_card_jail_free(player, 0)
    assert player.get_out_of_jail_cards == 1

    game._apply_card_jail(player, 0)
    assert player.in_jail is True


def test_game_check_bankruptcy_releases_assets_and_removes_player():
    game = Game(["A", "B"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    player.balance = 0

    game._check_bankruptcy(player)

    assert player not in game.players
    assert prop.owner is None
    assert prop.is_mortgaged is False


def test_game_apply_card_dispatch_unknown_action_is_noop():
    game = Game(["A", "B"])
    player = game.players[0]
    start = player.balance

    game._apply_card(player, {"description": "noop", "action": "unknown", "value": 999})

    assert player.balance == start


def test_dice_describe_and_repr_paths(monkeypatch):
    dice = Dice()

    seq = iter([3, 3, 2, 5])
    monkeypatch.setattr("random.randint", lambda _a, _b: next(seq))

    dice.roll()
    assert "DOUBLES" in dice.describe()
    assert dice.doubles_streak == 1

    dice.roll()
    assert "DOUBLES" not in dice.describe()
    assert dice.doubles_streak == 0
    assert "Dice(" in repr(dice)


def test_bank_summary_and_repr(capsys):
    bank = Bank()
    bank.collect(100)
    bank.summary()
    out = capsys.readouterr().out

    assert "Bank reserves" in out
    assert "Loans issued" in out
    assert "Bank(" in repr(bank)


def test_cards_reshuffle_and_repr_non_empty(monkeypatch):
    cards = [{"v": 1}, {"v": 2}, {"v": 3}]
    deck = CardDeck(cards)

    monkeypatch.setattr("random.shuffle", lambda c: c.reverse())
    deck.reshuffle()

    assert deck.draw()["v"] == 3
    assert "CardDeck(" in repr(deck)


def test_board_is_purchasable_false_for_non_property_position():
    board = Board()

    assert board.is_purchasable(0) is False


def test_ui_player_card_jail_cards_and_properties_branch(capsys):
    p = Player("A")
    p.in_jail = True
    p.jail_turns = 1
    p.get_out_of_jail_cards = 1
    prop = Board().get_property_at(1)
    prop.owner = p
    p.add_property(prop)

    ui.print_player_card(p)
    out = capsys.readouterr().out

    assert "IN JAIL" in out
    assert "Jail cards" in out
    assert "Properties:" in out


def test_ui_functions_and_input_branches(monkeypatch, capsys):
    p = Player("A")
    ui.print_banner("B")
    ui.print_player_card(p)
    ui.print_standings([p])
    ui.print_board_ownership(Board())
    out = capsys.readouterr().out
    assert "Player" in out

    assert ui.format_currency(1500) == "$1,500"

    monkeypatch.setattr("builtins.input", lambda _p: "12")
    assert ui.safe_int_input("x", default=0) == 12

    monkeypatch.setattr("builtins.input", lambda _p: "not-int")
    assert ui.safe_int_input("x", default=7) == 7

    monkeypatch.setattr("builtins.input", lambda _p: "y")
    assert ui.confirm("x") is True
    monkeypatch.setattr("builtins.input", lambda _p: "n")
    assert ui.confirm("x") is False


def test_main_get_player_names_and_main_error_branches(monkeypatch, capsys):
    main_mod = importlib.import_module("main")

    monkeypatch.setattr("builtins.input", lambda _p: " Alice, , Bob ,, ")
    names = main_mod.get_player_names()
    assert names == ["Alice", "Bob"]

    class FakeGameKeyboard:
        def __init__(self, _names):
            pass

        def run(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(main_mod, "Game", FakeGameKeyboard)
    main_mod.main()
    assert "interrupted" in capsys.readouterr().out.lower()

    class FakeGameValue:
        def __init__(self, _names):
            raise ValueError("bad setup")

    monkeypatch.setattr(main_mod, "Game", FakeGameValue)
    main_mod.main()
    assert "setup error" in capsys.readouterr().out.lower()


def test_main_dunder_main_branch_executes(monkeypatch):
    class FakeGame:
        def __init__(self, _names):
            pass

        def run(self):
            return None

    monkeypatch.setattr("builtins.input", lambda _p: "A,B")
    monkeypatch.setattr("moneypoly.game.Game", FakeGame)
    runpy.run_module("main", run_name="__main__")


def test_play_turn_branch_three_doubles_sends_to_jail(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]

    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    game.dice.doubles_streak = 3

    game.play_turn()

    assert p.in_jail is True


def test_play_turn_branch_doubles_gets_extra_turn(monkeypatch):
    game = Game(["A", "B"])
    start_index = game.current_index

    monkeypatch.setattr(game.dice, "roll", lambda: 1)
    monkeypatch.setattr(game.dice, "describe", lambda: "1 + 0 = 1")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: True)
    game.dice.doubles_streak = 0
    monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _r: None)

    game.play_turn()

    assert game.current_index == start_index


def test_move_and_resolve_branch_paths(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]

    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 30))
    game._move_and_resolve(p, 1)
    assert p.in_jail is True

    p.in_jail = False
    p.position = 0
    start = p.balance
    bank_start = game.bank.get_balance()
    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 38))
    game._move_and_resolve(p, 1)
    assert p.balance == start - 75
    assert game.bank.get_balance() == bank_start + 75

    called = {"chance": 0, "cc": 0, "prop": 0}

    monkeypatch.setattr(game.card_decks["chance"], "draw", lambda: {"description": "d", "action": "collect", "value": 1})
    monkeypatch.setattr(game.card_decks["community_chest"], "draw", lambda: {"description": "d", "action": "collect", "value": 1})

    def fake_apply(_pl, card):
        if card["action"] == "collect":
            called["chance"] += 1

    monkeypatch.setattr(game, "_apply_card", fake_apply)

    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 7))
    game._move_and_resolve(p, 1)
    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 2))
    game._move_and_resolve(p, 1)
    assert called["chance"] == 2

    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 20))
    game._move_and_resolve(p, 1)

    def fake_handle(_pl, _prop):
        called["prop"] += 1

    monkeypatch.setattr(game, "_handle_property_tile", fake_handle)
    monkeypatch.setattr(game.board, "get_property_at", lambda _pos: object())

    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 5))
    game._move_and_resolve(p, 1)
    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 1))
    game._move_and_resolve(p, 1)
    assert called["prop"] == 2

    # Cover railroad/property branches where lookup unexpectedly returns None.
    monkeypatch.setattr(game.board, "get_property_at", lambda _pos: None)
    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 5))
    game._move_and_resolve(p, 1)
    monkeypatch.setattr(p, "move", lambda _s: setattr(p, "position", 1))
    game._move_and_resolve(p, 1)


def test_handle_property_tile_buy_auction_skip_and_rent(monkeypatch):
    game = Game(["A", "B"])
    a, b = game.players
    prop = game.board.get_property_at(1)

    monkeypatch.setattr("builtins.input", lambda _p: "b")
    bought = {"n": 0}
    monkeypatch.setattr(game, "buy_property", lambda _pl, _pr: bought.__setitem__("n", 1))
    game._handle_property_tile(a, prop)
    assert bought["n"] == 1

    monkeypatch.setattr("builtins.input", lambda _p: "a")
    auctioned = {"n": 0}
    monkeypatch.setattr(game, "auction_property", lambda _pr: auctioned.__setitem__("n", 1))
    game._handle_property_tile(a, prop)
    assert auctioned["n"] == 1

    monkeypatch.setattr("builtins.input", lambda _p: "s")
    game._handle_property_tile(a, prop)

    prop.owner = a
    game._handle_property_tile(a, prop)

    prop.owner = b
    rent_called = {"n": 0}
    monkeypatch.setattr(game, "pay_rent", lambda _pl, _pr: rent_called.__setitem__("n", 1))
    game._handle_property_tile(a, prop)
    assert rent_called["n"] == 1


def test_pay_rent_branches(monkeypatch):
    game = Game(["A", "B"])
    tenant, owner = game.players
    prop = game.board.get_property_at(1)

    prop.is_mortgaged = True
    game.pay_rent(tenant, prop)

    prop.is_mortgaged = False
    prop.owner = None
    game.pay_rent(tenant, prop)

    prop.owner = owner
    monkeypatch.setattr(prop, "get_rent", lambda: 50)
    tenant_start = tenant.balance
    owner_start = owner.balance
    game.pay_rent(tenant, prop)
    assert tenant.balance == tenant_start - 50
    assert owner.balance == owner_start + 50


def test_mortgage_and_unmortgage_guard_branches():
    game = Game(["A", "B"])
    a, b = game.players
    prop = game.board.get_property_at(1)

    assert game.mortgage_property(a, prop) is False

    prop.owner = a
    prop.is_mortgaged = True
    assert game.mortgage_property(a, prop) is False

    prop.is_mortgaged = False
    assert game.unmortgage_property(b, prop) is False

    assert game.unmortgage_property(a, prop) is False


def test_unmortgage_success_branch_updates_balances():
    game = Game(["A", "B"])
    a = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = a
    a.add_property(prop)
    prop.mortgage()
    a.balance = 200
    bank_start = game.bank.get_balance()

    ok = game.unmortgage_property(a, prop)

    assert ok is True
    assert prop.is_mortgaged is False
    assert game.bank.get_balance() > bank_start


def test_trade_guard_branches():
    game = Game(["A", "B"])
    a, b = game.players
    prop = game.board.get_property_at(1)

    assert game.trade(a, b, prop, 100) is False

    prop.owner = a
    b.balance = 10
    assert game.trade(a, b, prop, 100) is False


def test_auction_no_bids_branch(monkeypatch):
    game = Game(["A", "B"])
    prop = game.board.get_property_at(1)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 0)

    game.auction_property(prop)

    assert prop.owner is None


def test_auction_cannot_afford_branch(monkeypatch):
    game = Game(["A", "B"])
    prop = game.board.get_property_at(1)
    game.players[0].balance = 10

    bids = iter([200, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: next(bids))

    game.auction_property(prop)

    assert prop.owner is None


def test_handle_jail_turn_use_card_and_serve_turn_paths(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]
    p.in_jail = True
    p.get_out_of_jail_cards = 1

    responses = iter([True])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _p: next(responses))
    monkeypatch.setattr(game.dice, "roll", lambda: 2)
    monkeypatch.setattr(game.dice, "describe", lambda: "1 + 1 = 2")
    monkeypatch.setattr(game, "_move_and_resolve", lambda _pl, _r: None)

    game._handle_jail_turn(p)
    assert p.in_jail is False
    assert p.get_out_of_jail_cards == 0

    p.in_jail = True
    p.jail_turns = 0
    p.get_out_of_jail_cards = 0
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _p: False)
    game._handle_jail_turn(p)
    assert p.jail_turns == 1


def test_handle_jail_turn_decline_card_then_pay_fine(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]
    p.in_jail = True
    p.get_out_of_jail_cards = 1
    start = p.balance

    answers = iter([False, True])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _p: next(answers))
    monkeypatch.setattr(game.dice, "roll", lambda: 2)
    monkeypatch.setattr(game.dice, "describe", lambda: "1 + 1 = 2")
    monkeypatch.setattr(game, "_move_and_resolve", lambda _pl, _r: None)

    game._handle_jail_turn(p)

    assert p.in_jail is False
    assert p.balance == start


def test_apply_card_move_to_property_branch(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]
    p.position = 10
    called = {"n": 0}

    monkeypatch.setattr(game.board, "get_tile_type", lambda _v: "property")
    monkeypatch.setattr(game.board, "get_property_at", lambda _v: object())
    monkeypatch.setattr(game, "_handle_property_tile", lambda _pl, _pr: called.__setitem__("n", 1))

    game._apply_card_move_to(p, 1)

    assert called["n"] == 1


def test_apply_card_move_to_property_with_none_lookup(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]

    monkeypatch.setattr(game.board, "get_tile_type", lambda _v: "property")
    monkeypatch.setattr(game.board, "get_property_at", lambda _v: None)

    game._apply_card_move_to(p, 1)


def test_apply_card_dispatch_actions(monkeypatch):
    game = Game(["A", "B"])
    p = game.players[0]
    called = {k: 0 for k in ["collect", "pay", "jail", "jail_free", "move_to", "xfer"]}

    monkeypatch.setattr(game, "_apply_card_collect", lambda _p, _v: called.__setitem__("collect", 1))
    monkeypatch.setattr(game, "_apply_card_pay", lambda _p, _v: called.__setitem__("pay", 1))
    monkeypatch.setattr(game, "_apply_card_jail", lambda _p, _v: called.__setitem__("jail", 1))
    monkeypatch.setattr(game, "_apply_card_jail_free", lambda _p, _v: called.__setitem__("jail_free", 1))
    monkeypatch.setattr(game, "_apply_card_move_to", lambda _p, _v: called.__setitem__("move_to", 1))
    monkeypatch.setattr(game, "_apply_card_transfer_from_all", lambda _p, _v: called.__setitem__("xfer", called["xfer"] + 1))

    game._apply_card(p, {"description": "c", "action": "collect", "value": 1})
    game._apply_card(p, {"description": "p", "action": "pay", "value": 1})
    game._apply_card(p, {"description": "j", "action": "jail", "value": 0})
    game._apply_card(p, {"description": "jf", "action": "jail_free", "value": 0})
    game._apply_card(p, {"description": "m", "action": "move_to", "value": 1})
    game._apply_card(p, {"description": "b", "action": "birthday", "value": 1})
    game._apply_card(p, {"description": "cf", "action": "collect_from_all", "value": 1})

    assert called["collect"] == 1
    assert called["pay"] == 1
    assert called["jail"] == 1
    assert called["jail_free"] == 1
    assert called["move_to"] == 1
    assert called["xfer"] == 2


def test_apply_card_collect_success_and_none_card_branch():
    game = Game(["A", "B"])
    p = game.players[0]
    start = p.balance

    game._apply_card_collect(p, 10)
    game._apply_card(p, None)

    assert p.balance == start + 10


def test_check_bankruptcy_non_bankrupt_no_change():
    game = Game(["A", "B"])
    p = game.players[0]
    before = list(game.players)

    game._check_bankruptcy(p)

    assert game.players == before


def test_check_bankruptcy_when_player_not_in_players_list():
    game = Game(["A", "B"])
    ghost = Player("ghost")
    ghost.balance = 0

    game._check_bankruptcy(ghost)

    assert ghost not in game.players


def test_run_paths_winner_and_no_players(monkeypatch):
    game = Game(["A", "B"])

    monkeypatch.setattr(game, "play_turn", lambda: setattr(game, "turn_number", 100))
    monkeypatch.setattr(game, "find_winner", lambda: game.players[0])
    game.run()

    game2 = Game(["A"])
    monkeypatch.setattr(game2, "find_winner", lambda: None)
    game2.run()


def test_interactive_menu_and_submenus(monkeypatch):
    game = Game(["A", "B"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)

    choices = iter([1, 2, 3, 4, 5, 6, 100, 0])

    def fake_safe_int(_prompt, default=0):
        return next(choices)

    monkeypatch.setattr("moneypoly.ui.safe_int_input", fake_safe_int)
    monkeypatch.setattr(game, "_menu_mortgage", lambda _p: None)
    monkeypatch.setattr(game, "_menu_unmortgage", lambda _p: None)
    monkeypatch.setattr(game, "_menu_trade", lambda _p: None)
    monkeypatch.setattr("moneypoly.ui.print_standings", lambda _ps: None)
    monkeypatch.setattr("moneypoly.ui.print_board_ownership", lambda _b: None)

    loaned = {"n": 0}
    monkeypatch.setattr(game.bank, "give_loan", lambda _p, _a: loaned.__setitem__("n", 1))

    game.interactive_menu(player)

    assert loaned["n"] == 1


def test_interactive_menu_choice_6_non_positive_amount(monkeypatch):
    game = Game(["A", "B"])
    player = game.players[0]

    values = iter([6, 0, 0])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: next(values))
    called = {"n": 0}
    monkeypatch.setattr(game.bank, "give_loan", lambda _p, _a: called.__setitem__("n", 1))

    game.interactive_menu(player)

    assert called["n"] == 0


def test_menu_functions_guard_and_selection_paths(monkeypatch):
    game = Game(["A", "B"])
    a, b = game.players

    # Mortgage menu: empty and select path
    game._menu_mortgage(a)
    p = game.board.get_property_at(1)
    p.owner = a
    a.add_property(p)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 1)
    called = {"m": 0, "u": 0, "t": 0}
    monkeypatch.setattr(game, "mortgage_property", lambda _pl, _pr: called.__setitem__("m", 1))
    game._menu_mortgage(a)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 99)
    game._menu_mortgage(a)

    # Unmortgage menu: empty and select path
    game._menu_unmortgage(a)
    p.is_mortgaged = True
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 1)
    monkeypatch.setattr(game, "unmortgage_property", lambda _pl, _pr: called.__setitem__("u", 1))
    game._menu_unmortgage(a)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 99)
    game._menu_unmortgage(a)

    # Trade menu branches
    game_single = Game(["solo"])
    game_single._menu_trade(game_single.players[0])

    no_props_game = Game(["A", "B"])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 1)
    no_props_game._menu_trade(no_props_game.players[0])

    bad_partner_game = Game(["A", "B"])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: 99)
    bad_partner_game._menu_trade(bad_partner_game.players[0])

    a_prop_game = Game(["A", "B"])
    seller = a_prop_game.players[0]
    prop2 = a_prop_game.board.get_property_at(1)
    prop2.owner = seller
    seller.add_property(prop2)

    values = iter([1, 1, 99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: next(values))
    monkeypatch.setattr(a_prop_game, "trade", lambda _s, _b, _p, _c: called.__setitem__("t", 1))
    a_prop_game._menu_trade(seller)

    values_bad_prop = iter([1, 99])
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: next(values_bad_prop))
    a_prop_game._menu_trade(seller)

    assert called == {"m": 1, "u": 1, "t": 1}


def test_player_negative_money_operations_raise():
    p = Player("A")
    with pytest.raises(ValueError):
        p.add_money(-1)
    with pytest.raises(ValueError):
        p.deduct_money(-1)


def test_player_remove_absent_property_and_property_repr():
    p = Player("A")
    prop = Board().get_property_at(1)
    p.remove_property(prop)
    assert "Property(" in repr(prop)


def test_property_group_all_owned_by_none_and_repr():
    board = Board()
    group = board.groups["brown"]
    assert group.all_owned_by(None) is False
    assert "PropertyGroup(" in repr(group)


def _game_two_players():
    return Game(["A", "B"])


def test_error_1_railroads_are_backed_by_purchasable_properties():
    board = Board()
    for pos in (5, 15, 25, 35):
        assert board.get_property_at(pos) is not None
        assert board.is_purchasable(pos) is True


def test_error_2_jail_voluntary_fine_deducts_player_cash(monkeypatch):
    game = _game_two_players()
    player = game.players[0]
    player.in_jail = True

    start_player = player.balance
    start_bank = game.bank.get_balance()

    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: True)
    monkeypatch.setattr(game.dice, "roll", lambda: 3)
    monkeypatch.setattr(game.dice, "describe", lambda: "1 + 2 = 3")
    monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _r: None)

    game._handle_jail_turn(player)

    assert player.balance == start_player - JAIL_FINE
    assert game.bank.get_balance() == start_bank + JAIL_FINE


def test_error_3_find_winner_returns_richest_player():
    game = Game(["A", "B"])
    game.players[0].balance = 500
    game.players[1].balance = 1500

    assert game.find_winner().name == "B"


def test_error_4_player_move_awards_salary_when_passing_go():
    player = Player("A")
    player.position = 39
    start = player.balance

    end_pos = player.move(2)

    assert end_pos == 1
    assert player.balance == start + GO_SALARY


def test_error_5_trade_transfers_cash_to_seller():
    game = _game_two_players()
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = seller
    seller.add_property(prop)

    seller_start = seller.balance
    buyer_start = buyer.balance

    ok = game.trade(seller, buyer, prop, 120)

    assert ok is True
    assert seller.balance == seller_start + 120
    assert buyer.balance == buyer_start - 120
    assert prop.owner == buyer


def test_error_6_buy_property_allows_exact_cash():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    player.balance = prop.price

    ok = game.buy_property(player, prop)

    assert ok is True
    assert prop.owner == player
    assert prop in player.properties


def test_error_7_dice_roll_uses_full_six_sided_range(monkeypatch):
    calls = []

    def fake_randint(low, high):
        calls.append((low, high))
        return 1

    monkeypatch.setattr("random.randint", fake_randint)

    dice = Dice()
    dice.roll()

    assert calls == [(1, 6), (1, 6)]


def test_error_8_bank_loan_reduces_bank_funds():
    bank = Bank()
    player = Player("A")
    start_bank = bank.get_balance()

    bank.give_loan(player, 200)

    assert player.balance == 1500 + 200
    assert bank.get_balance() == start_bank - 200


def test_error_9_trade_rejects_non_positive_cash_without_exception():
    game = _game_two_players()
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = seller
    seller.add_property(prop)

    assert game.trade(seller, buyer, prop, 0) is False
    assert game.trade(seller, buyer, prop, -50) is False
    assert prop.owner == seller


def test_error_11_net_worth_includes_property_values():
    player = Player("A")
    group = PropertyGroup("Brown", "brown")
    p1 = Property("P1", 1, 120, 10, group)
    p2 = Property("P2", 3, 180, 14, group)
    player.properties.extend([p1, p2])

    assert player.net_worth() == player.balance + 120 + 180


def test_error_12_bank_collect_ignores_negative_amounts():
    bank = Bank()
    start = bank.get_balance()

    bank.collect(-150)

    assert bank.get_balance() == start


def test_error_14_mortgage_uses_payout_flow_not_negative_collect_side_effects():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    start_collected = game.bank._total_collected

    ok = game.mortgage_property(player, prop)

    assert ok is True
    assert game.bank._total_collected == start_collected


def test_error_15_trade_rejects_self_trade():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)

    ok = game.trade(player, player, prop, 100)

    assert ok is False
    assert prop.owner == player


def test_error_16_mortgage_fails_gracefully_when_bank_cannot_pay():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    game.bank._funds = 0

    ok = game.mortgage_property(player, prop)

    assert ok is False
    assert prop.is_mortgaged is False


def test_error_17_collect_from_all_charges_every_other_player():
    game = Game(["A", "B", "C"])
    collector = game.players[0]
    low = game.players[1]
    rich = game.players[2]
    low.balance = 5
    rich.balance = 30

    game._apply_card_transfer_from_all(collector, 10)

    assert low.balance == -5
    assert rich.balance == 20
    assert collector.balance == 1500 + 20


def test_error_18_collect_card_handles_insufficient_bank_without_crash():
    game = _game_two_players()
    player = game.players[0]
    game.bank._funds = 0
    start = player.balance

    try:
        game._apply_card_collect(player, 200)
    except ValueError as exc:  # pragma: no cover - this is the bug path
        pytest.fail(f"collect-card payout should not raise, got: {exc}")

    assert player.balance == start


def test_error_19_move_to_card_applies_go_to_jail_effects():
    game = _game_two_players()
    player = game.players[0]

    game._apply_card_move_to(player, 30)

    assert player.in_jail is True
    assert player.position == 10


def test_error_20_loan_rejects_overdraw_requests():
    bank = Bank()
    player = Player("A")
    bank._funds = 100
    start_player = player.balance

    bank.give_loan(player, 150)

    assert bank.get_balance() == 100
    assert player.balance == start_player
    assert bank.loan_count() == 0


def test_error_21_advance_to_go_always_awards_salary_even_from_go():
    game = _game_two_players()
    player = game.players[0]
    player.position = 0
    start = player.balance

    game._apply_card_move_to(player, 0)

    assert player.balance == start + GO_SALARY


def test_error_24_buy_rejects_already_owned_property():
    game = _game_two_players()
    owner, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)

    ok = game.buy_property(buyer, prop)

    assert ok is False
    assert prop.owner == owner


def test_error_25_failed_unmortgage_keeps_property_mortgaged():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    prop.mortgage()
    player.balance = 0

    ok = game.unmortgage_property(player, prop)

    assert ok is False
    assert prop.is_mortgaged is True


def test_error_26_buy_rejects_mortgaged_property_even_if_unowned():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.is_mortgaged = True
    prop.owner = None

    ok = game.buy_property(player, prop)

    assert ok is False
    assert prop.owner is None


def test_error_27_play_turn_safe_when_last_player_eliminated(monkeypatch):
    game = Game(["Solo"])
    player = game.players[0]
    player.balance = 100

    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    game.dice.doubles_streak = 0

    try:
        game.play_turn()
    except ZeroDivisionError as exc:  # pragma: no cover - this is the bug path
        pytest.fail(f"play_turn should not crash when player list becomes empty: {exc}")

    assert game.players == []


def test_error_28_turn_order_kept_after_current_player_elimination(monkeypatch):
    game = Game(["A", "B", "C"])
    a = game.players[0]
    a.balance = 100

    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    game.dice.doubles_streak = 0

    game.play_turn()

    assert [p.name for p in game.players] == ["B", "C"]
    assert game.current_index == 0


def test_error_30_turn_order_kept_when_jailed_current_player_eliminated(monkeypatch):
    game = Game(["A", "B", "C"])
    a = game.players[0]
    a.in_jail = True
    a.jail_turns = 2
    a.balance = 10

    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: False)
    monkeypatch.setattr(game.dice, "roll", lambda: 0)
    monkeypatch.setattr(game.dice, "describe", lambda: "0 + 0 = 0")

    game.play_turn()

    assert [p.name for p in game.players] == ["B", "C"]
    assert game.current_index == 0


def test_error_31_auction_rejects_already_owned_property(monkeypatch):
    game = Game(["Owner", "Bidder"])
    owner, bidder = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)
    owner_start = owner.balance

    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 200)

    game.auction_property(prop)

    assert prop.owner == owner
    assert owner.balance == owner_start
    assert prop not in bidder.properties


def test_branch_sanity_find_winner_returns_none_for_empty_player_list():
    game = Game(["A"])
    game.players = []

    assert game.find_winner() is None


def test_branch_sanity_buy_property_rejects_insufficient_cash():
    game = _game_two_players()
    player = game.players[0]
    prop = game.board.get_property_at(1)
    player.balance = prop.price - 1

    assert game.buy_property(player, prop) is False


def test_branch_sanity_trade_rejects_unowned_by_seller():
    game = _game_two_players()
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = buyer

    assert game.trade(seller, buyer, prop, 100) is False


def test_branch_sanity_bank_collect_positive_increases_balance():
    bank = Bank()
    start = bank.get_balance()

    bank.collect(100)

    assert bank.get_balance() == start + 100


def test_branch_sanity_player_move_lands_on_go_gets_salary():
    player = Player("A")
    player.position = 39
    start = player.balance

    player.move(1)

    assert player.position == 0
    assert player.balance == start + GO_SALARY


def test_branch_sanity_income_tax_path_collects_to_bank(monkeypatch):
    game = _game_two_players()
    player = game.players[0]

    start_player = player.balance
    start_bank = game.bank.get_balance()

    game._move_and_resolve(player, 4)

    assert player.balance == start_player - INCOME_TAX_AMOUNT
    assert game.bank.get_balance() == start_bank + INCOME_TAX_AMOUNT
