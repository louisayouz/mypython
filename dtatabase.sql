CREATE SEQUENCE portfolios_id_seq;
 CREATE TABLE IF NOT EXISTS portfolios (
    id integer NOT NULL DEFAULT nextval('portfolios_id_seq'::regclass),
    user_id integer NOT NULL,
    portfolio_name character varying(255),
	created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT portfolios_pkey PRIMARY KEY (id),
	CONSTRAINT portfolios_name_key UNIQUE (portfolio_name)

);
CREATE SEQUENCE portfolios_id_seq;
CREATE TABLE portfolio_quotes (
    id integer NOT NULL DEFAULT nextval('portfolio_quotes_id_seq'::regclass),
    portfolio_id integer NOT NULL,
    quote_name character varying(32),
	buy_price numeric(8,3),
	buy_count integer,

	created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT portfolio_quotes_pkey PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS index_portfolio_quotes_on_portfolio_id_quote_name
ON public.portfolio_quotes USING btree
(portfolio_id, quote_name,  from_year, from_month)
WHERE from_year IS NOT NULL AND from_month IS NOT NULL;

CREATE SEQUENCE quote_dividents_id_seq;
CREATE TABLE quote_dividents (
    id integer NOT NULL DEFAULT nextval('quote_dividents_id_seq'::regclass),
    quote_name character varying(32),
	  div_price numeric(8,3),
	  pay_year integer,
	  pay_month integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT quote_dividents_key UNIQUE (quote_name, pay_year, pay_month)
);

ALTER TABLE portfolio_quotes
	ADD COLUMN from_year INTEGER CHECK (from_year BETWEEN 2010 AND 2100),
	ADD COLUMN from_month SMALLINT CHECK (from_month BETWEEN 1 AND 12),
	ADD COLUMN to_year INTEGER CHECK (to_year BETWEEN 2010 AND 2100),
	ADD COLUMN to_month  SMALLINT CHECK (to_month BETWEEN 1 AND 12);

CREATE SEQUENCE quotes_id_seq;
CREATE TABLE quotes (
    id integer NOT NULL DEFAULT nextval('quotes_id_seq'::regclass),
    quote_name character varying(32),
	created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT quote_names UNIQUE (quote_name)
);