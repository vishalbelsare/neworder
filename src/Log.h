
#pragma once

#include "NewOrder.h"

#include <string>
#include <type_traits>
#include <sstream>
//#include <chrono>
#include <iomanip>

using namespace std::string_literals;

namespace std
{
std::string to_string(const std::string& str);

std::string to_string(const py::object& o);

template<typename T>
std::string to_string(const std::vector<T>& v)
{
  if (v.empty())
    return "[]";
  std::string result = "[" + std::to_string(v[0]);

  for (size_t i = 1; i < v.size(); ++i)
    result += ", " + std::to_string(v[i]);
  result += "]";

  return result;
}

}


// need an rvalue ref as might/will be a temporary
template<typename T>
std::string operator%(std::string&& str, T value)
{
  size_t s = str.find("%%");
  if (s != std::string::npos)
  {
    str.replace(s, 2, std::to_string(value));
  }
  return std::move(str);
}

// formatters
namespace format {

  // format floating point to __x.yz
  template<typename T>
  std::string decimal(T x, int pad, int places)
  {
    static_assert(std::is_floating_point<T>::value, "decimal formatting requires a floating-point type");
    std::ostringstream str;
    str.precision(places);
    str << std::fixed << std::setw(pad + places + 1) << x;
    return str.str();
  }

  // pad integral types
  template<typename T>
  std::string pad(T x, int width, char padchar=' ')
  {
    static_assert(std::is_integral<T>::value, "padding requires an integral type");
    std::ostringstream str;
    str << std::setfill(padchar) << std::setw(width) << x;
    return str.str();
  }

  // integral types in hex (zero padded, width implied from size of T, prefix is '0x' if specified)
  template<typename T>
  std::string hex(T x, bool prefix=true)
  {
    static_assert(std::is_integral<T>::value, "hex formatting requires an integral type");
    constexpr int width = (sizeof(T) << 1); // e.g. 32bits=4bytes -> 8 chars

    std::ostringstream str;
    str << (prefix ? "0x": "") << std::setfill('0') << std::setw(width) << std::hex << x;
    return str.str();
  }

  // boolean type as string "true" or "false"
  inline std::string boolean(bool x)
  {
    return x ? "true" : "false";
  }

}

namespace no {

// msg is forcibly coerced to a string
NEWORDER_EXPORT void log(const py::handle& msg);

void log(const std::string& msg);
void warn(const std::string& msg);

}
