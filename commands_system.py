import inspect
import traceback

def command(name=None, aliases=None, before=None, after=None):
    def decorator(func):
        nonlocal name, aliases, before, after
        if name is None:
            name = func.__name__
        if aliases is None:
            aliases = []

        command = Command(func, name, aliases, before, after)
        commands.append(command)
        return func

    return decorator

async def process_commands(message: guilded.Message):
    for command in commands:
        if await command.check(message):
            return

class Context:
    def __init__(self, message: guilded.Message, args: List[str]):
        self.message = message
        self.args = args
        self.kwargs = None
        self.author = message.author
        self.channel = message.channel
        self.guild = message.guild
        self.send = message.channel.send
        self.reply = message.reply

class Command():
    def __init__(self, func: Callable, name: str, aliases: List[str], before: Callable = None, after: Callable = None):
        self.name = name
        self.aliases = aliases
        self.callables = aliases
        self.callables.append(name)
        self.invokable = func
        self.signature = inspect.signature(func)

    async def check(self, message: guilded.Message):
        for callable in self.callables:
            if message.content.startswith(f"{prefix}{callable} "):
                return await self._invoke(message)

    async def _invoke(self, message: guilded.Message):
        args_str = message.content[len(prefix) + len(self.name) + 1:]
        context = Context(message, [])
        args = await self._parse_args(context, args_str, message)
        await self.invokable(context, *args)
        return True

    async def _parse_args(self, ctx: Context, args_str: str, message: guilded.Message):
        args = []
        ctx.kwargs = {}
        kwargs = ctx.kwargs
        ctx.args = args
        params = list(self.signature.parameters.values())[1:]

        for param in params:
            arg_name = param.name
            arg_type = param.annotation

            if arg_name == "ctx":
                continue

            if arg_type is inspect.Parameter.empty:
                arg_value, _, args_str = args_str.partition(' ')
                args.append(arg_value)
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                args.append(args_str.strip())
                break
            else:
                if arg_type is int:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(int(arg_value))
                elif arg_type is float:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(float(arg_value))
                elif arg_type is bool:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(arg_value.lower() == 'true')
                elif arg_type is guilded.Message:
                    args.append(message)
                elif arg_type is guilded.User:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(await client.getch_user(arg_value))
                elif arg_type is guilded.Member:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(await ctx.guild.getch_member(arg_value))
                elif arg_type is guilded.ChatChannel:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(await client.getch_channel(arg_value))
                else:
                    arg_value, _, args_str = args_str.partition(' ')
                    args.append(arg_value)

        return args
