:- module(harmony, [
    struct/1,
    class/1,
    group/5,
    tmpl/2,
    chord/2,
    group_notation//1,
    struct_interval/2,
    group_class/2,
    group_key_tmpl/3,
    tmpl_chord/2,
    group_key_chord/3,
    clsfrom_to/2,
    grpfrom_to/2,
    group_string/2,
    predict/6,
    reverse/6,
    connect/10
]).
:- use_module(library(lists)).
:- set_prolog_flag(double_quotes, codes).

:- discontiguous(group/5).
:- discontiguous(group_class/2).
:- discontiguous(term_expansion/2).

note('1', 0).
note('b2', 1).
note('2', 2).
note('b3', 3).
note('3', 4).
note('4', 5).
note('b5', 6).
note('5', 7).
note('b6', 8).
note('6', 9).
note('b7', 10).
note('7', 11).
tritone(X, Y) :-
    note(X, A),
    B is (A + 6) mod 12,
    note(Y, B).

note_name('C', 0).
note_name('C#', 1).
note_name('D', 2).
note_name('D#', 3).
note_name('E', 4).
note_name('F', 5).
note_name('F#', 6).
note_name('G', 7).
note_name('G#', 8).
note_name('A', 9).
note_name('A#', 10).
note_name('B', 11).

struct('S').
struct('s').
struct('T').
struct('t').
struct('D').
struct('d').

class('S').
class('T').
class('D').
class('Dt').
class('Dd').

struct_interval(struct('S'), [0, 2, 4, 5, 7, 9, 11]).
struct_interval(struct('s'), [0, 2, 3, 5, 7, 8, 10]).
struct_interval(struct('T'), [0, 2, 4, 6, 7, 9, 11]).
struct_interval(struct('t'), [0, 2, 3, 5, 7, 9, 10]).
struct_interval(struct('D'), [0, 2, 4, 5, 7, 9, 10]).
struct_interval(struct('d'), [0, 1, 4, 5, 7, 8, 10]).

group(struct('S'), [], [], '1', 3).
group(struct('S'), [], [13], '1', 3).
group(struct('s'), [], [], '6', 1).
group(struct('T'), [], [], '4', 1).
group(struct('t'), [], [], '2', 1).
group(struct('D'), [], [9], '5', 9).
group(struct('D'), [], [], '5', 3).
group(struct('d'), [], [11], '3', 11).
group(struct('d'), [], [], '3', 5).
group(struct('D'), [], [], '1', 7).
group(struct('D'), [], [9], '1', 9).
group(struct('D'), [7], [], '1', 3).
group(struct('d'), [], [], '6', 9).
group(struct('d'), [7, 9], [], '6', 3).
group(struct('d'), [9], [], '6', 3).
group(struct('d'), [], [11], '6', 11).
group(struct('D'), [7], [], '5', 7).
group(struct('d'), [], [], '5', 9).
group(struct('d'), [7, 9], [], '3', 9).

group_notation(group(struct(St), S, F, H, R)) -->
    {group(struct(St), S, F, H, R), atom_codes(St, StCodes), add_prefix("#", S, AddS), add_prefix("b", F, AddF), atom_codes(H, HCodes), number_codes(R, RCodes)},
    StCodes, AddS, AddF, "(", HCodes, ",", RCodes, "°", ")".
add_prefix(Pre, S, AddS) :-
    maplist(ap_helper(Pre), S, Lst),
    flatten(Lst, AddS).
ap_helper(Pre, SEle, LstEle) :-
    number_codes(SEle, SEleCodes),
    append(Pre, SEleCodes, LstEle).

group_class(group(struct('S'), [], [], '1', 3), class('S')).
group_class(group(struct('S'), [], [13], '1', 3), class('S')).
group_class(group(struct('s'), [], [], '6', 1), class('S')).
group_class(group(struct('T'), [], [], '4', 1), class('T')).
group_class(group(struct('t'), [], [], '2', 1), class('T')).
group_class(group(struct('D'), [], [9], '5', 9), class('D')).
group_class(group(struct('D'), [], [], '5', 3), class('D')).
group_class(group(struct('d'), [], [11], '3', 11), class('D')).
group_class(group(struct('d'), [], [], '3', 5), class('D')).
group_class(group(struct('D'), [], [], '1', 7), class('Dt')).
group_class(group(struct('D'), [], [9], '1', 9), class('Dt')).
group_class(group(struct('D'), [7], [], '1', 3), class('Dt')).
group_class(group(struct('d'), [], [], '6', 9), class('Dt')).
group_class(group(struct('d'), [7, 9], [], '6', 3), class('Dt')).
group_class(group(struct('d'), [9], [], '6', 3), class('Dt')).
group_class(group(struct('d'), [], [11], '6', 11), class('Dt')).
group_class(group(struct('D'), [7], [], '5', 7), class('Dd')).
group_class(group(struct('d'), [], [], '5', 9), class('Dd')).
group_class(group(struct('d'), [7, 9], [], '3', 9), class('Dd')).

term_expansion(add_tritone, Generation) :-
    findall(group(St, S, F, H, R), (group(St, S, F, H, R), (St = struct('D'); St = struct('d'))), Groups),
    maplist(add_tritone_helper, Groups, NewLst),
    append(NewLst, Generation).
add_tritone_helper(
    group(St, S, F, H1, R),
    [
        group(St, S, F, H2, R),
        group_class(group(St, S, F, H2, R), C)
    ]
) :-
    tritone(H1, H2),
    group_class(group(St, S, F, H1, R), C).
add_tritone.

new_interval(Base, S, F, New) :-
    maplist(ni_helper(S, F), Base, New, [1, 9, 3, 11, 5, 13, 7]).
ni_helper(S, F, BaseEle, NewEle, Note) :-
    memberchk(Note, S) -> NewEle is BaseEle + 1;
    memberchk(Note, F) -> NewEle is BaseEle - 1;
    NewEle is BaseEle.

comptime_group_key_tmpl(group(St, S, F, H, R), Key, Tmpl) :-
    group(St, S, F, H, R),
    struct_interval(St, Interval),
    new_interval(Interval, S, F, NewInterval),
    note(H, Num1),
    note_name(Key, Num2),
    Delta is Num1 + Num2,
    maplist(gm_helper(Delta), NewInterval, Pitchs),
    Range is (R + 1) // 2,
    get_roots(Range, NewInterval, Delta, Roots),
    msort(Roots, SortedRoots),
    msort(Pitchs, SortedPitchs),
    Tmpl = tmpl(SortedRoots, SortedPitchs).
get_roots(Range, NewInterval, Delta, Roots) :-
    findall(X, (between(1, Range, Num), X is Num * 2 - 1), All),
    maplist(gr_helper(Delta, NewInterval), All, Roots).
gr_helper(Delta, NewInterval, AllEle, RootsEle) :-
    Index is AllEle mod 7,
    nth1(Index, NewInterval, IntervalEle),
    RootsEle is (IntervalEle + Delta) mod 12.
gm_helper(Delta, A, B) :-
    B is (A + Delta) mod 12.
term_expansion(group_key_tmpl, Generation) :-
    findall(group_key_tmpl(X, Y, Z), comptime_group_key_tmpl(X, Y, Z), All), sort(All, Generation), py_counter.
group_key_tmpl.

tmpl(R, P) :-
    group_key_tmpl(_, _, tmpl(R, P)).

is_subseq([], _).
is_subseq([H | T], [H | Rest]) :- 
    is_subseq(T, Rest).
is_subseq([H | T], [_ | Rest]) :- 
    is_subseq([H | T], Rest).

tmpl_chord(tmpl(R, P), chord(Root, Note)) :-
    tmpl(R, P),
    is_subseq(Note, P),
    intersection(R, Note, Pub),
    member(Root, Pub).

chord(R, N) :-
    tmpl_chord(_, chord(R, N)).

comptime_group_key_chord(G, K, C) :-
    group_key_tmpl(G, K, T),
    tmpl_chord(T, C).
term_expansion(group_key_chord, Generation) :-
    findall(group_key_chord(X, Y, Z), comptime_group_key_chord(X, Y, Z), All), sort(All, Generation), py_counter.
group_key_chord.

clsfrom_to(class('Dd'), class('D')).
clsfrom_to(class('D'), class('S')).
clsfrom_to(class('D'), class('Dt')).
clsfrom_to(class('S'), class('T')).
clsfrom_to(class('Dt'), class('T')).
clsfrom_to(class('T'), class('D')).
clsfrom_to(class('D'), class('D')).
clsfrom_to(class('Dd'), class('Dd')).
clsfrom_to(class('Dt'), class('Dt')).

comptime_grpfrom_to(A, B) :-
    group_class(A, X),
    group_class(B, Y),
    clsfrom_to(X, Y).
term_expansion(grpfrom_to, Generation) :-
    findall(grpfrom_to(X, Y), comptime_grpfrom_to(X, Y), All), sort(All, Generation), py_counter.
grpfrom_to.

comptime_group_string(G, S) :-
    phrase(group_notation(G), Codes),
    string_codes(S, Codes).
term_expansion(group_string, Generation) :-
    findall(group_string(X, Y), comptime_group_string(X, Y), All), sort(All, Generation), py_counter.
group_string.

predict(C, K, GN, NewTmplR, NewTmplN, NewG) :-
    group_key_chord(_G, K, C),
    grpfrom_to(_G, _NewG),
    group_string(_G, GN),
    group_key_tmpl(_NewG, K, tmpl(NewTmplR, NewTmplN)),
    group_string(_NewG, NewG).

reverse(C, K, GN, NewTmplR, NewTmplN, NewG) :-
    group_key_chord(_G, K, C),
    grpfrom_to(_NewG, _G),
    group_string(_G, GN),
    group_key_tmpl(_NewG, K, tmpl(NewTmplR, NewTmplN)),
    group_string(_NewG, NewG).

connect(C1, C2, G1, G2, K1, K2, NewG1, NewG2, NewTmplR, NewTmplN) :-
    group_key_chord(_G1, K1, C1),
    group_key_chord(_G2, K2, C2),
    _Tmpl = tmpl(NewTmplR, NewTmplN),
    group_key_tmpl(_NewG1, K1, _Tmpl),
    group_key_tmpl(_NewG2, K2, _Tmpl),
    grpfrom_to(_G1, _NewG1),
    grpfrom_to(_NewG2, _G2),
    group_string(_G1, G1),
    group_string(_G2, G2),
    group_string(_NewG1, NewG1),
    group_string(_NewG2, NewG2).
